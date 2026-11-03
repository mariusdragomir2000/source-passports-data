"""Turn enrich/gleif-matches.csv into one feed file that fills only empty fields.

usage: gleif_to_feed.py enrich/gleif-matches.csv batches/<out>.csv
- only unambiguous matches of entities GLEIF lists as ACTIVE;
- lapsed LEI records give only the registration number (an address or parent
  may have changed since); GLEIF creation dates are not used as founding years;
- matches made through a former or alternative name are listed, not used;
- only fields that are empty on the site (the 'missing' column);
- each layer's existing sources are kept and the GLEIF record is added, because
  the importer replaces a layer's source list with what the file gives.
Prints what it would fill and lists INACTIVE entities for a closure check.
"""
import csv, gzip, json, re, sys, datetime
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from gleif_lookup import norm

FORMS = set('sa spa ltd plc ag gmbh as nv bv sro vos oyj ab hf ehf zrt nyrt kft dd doo inc corp co llc pjsc jsc bm se kg limited'.split())


def core(name):
    """Normalised name without legal-form words or single letters (s r o, a s, d d)."""
    return [t for t in norm(name).split() if t not in FORMS and len(t) > 1]


def same_entity_name(ours, theirs):
    """True when GLEIF's current legal name is our legal name: equal apart from the
    legal form, a longer official form of it (Croatian, Hungarian), or a name written
    only in another script. A match made through a former or alternative name is not
    used: the entity may have been renamed, split or be a different body."""
    if not re.search('[A-Za-z]', theirs):
        return True
    a, b = core(ours), core(theirs)
    if a == b:
        return True
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    return len(short) >= 2 and long_[:len(short)] == short

R = '/home/claude/source-passports-data'
today = datetime.date.today().isoformat()
snap = json.load(gzip.open(R + '/mirror/passports-latest.json.gz'))
src = {p['id']: {L: v.get('sources') or [] for L, v in p['layers'].items()} for p in snap['passports']}
LIVE = {'ISSUED', 'PENDING_TRANSFER', 'PENDING_ARCHIVAL'}
rows, inactive, renamed, counts = [], [], [], {}
for m in csv.DictReader(open(sys.argv[1], encoding='utf-8')):
    if m['result'] != 'match':
        continue
    if m['entity_status'] != 'ACTIVE':
        if m['entity_status'] == 'INACTIVE':  # DUPLICATE records (no status) are skipped silently
            inactive.append(m)
        continue
    if not same_entity_name(m['legal_name'], m['gleif_legal_name']):
        renamed.append(m)
        continue
    miss = set(m['missing'].split())
    live = m['registration_status'] in LIVE
    vals = {}
    if 'registration_number' in miss and m['registered_as'].strip():
        vals['registration_number'] = m['registered_as'].strip()
    # GLEIF's entity creation date is often a later re-registration date
    # (BBC 2013, Petrobras 2005), so it is not used as the founding year.
    if live and 'registered_address' in miss and m['legal_address'].strip():
        vals['registered_address'] = m['legal_address'].strip()
    if live and 'parent_group' in miss and m['parent_name'].strip():
        vals['parent_group'] = m['parent_name'].strip() + ' (consolidating parent recorded in the GLEIF LEI register)'
    if not vals:
        continue
    line = ('GLEIF LEI register, record %s (%s), last updated %s, read %s | https://search.gleif.org/#/record/%s'
            % (m['lei'], m['gleif_legal_name'], m['last_update'][:10], today, m['lei']))
    row = {'mpm_id': m['mpm_id'], 'organisation': m['name'], 'name': '', 'country': m['country'], **vals}
    for layer, fields in (('origin', ('registration_number', 'year_founded', 'registered_address')), ('control', ('parent_group',))):
        if any(f in vals for f in fields):
            old = ['%s | %s' % (s['title'], s['url']) if s.get('url') else s['title'] for s in src.get(m['mpm_id'], {}).get(layer, [])]
            row['sources_' + layer] = '\n'.join(old + [line])
    for f in vals:
        counts[f] = counts.get(f, 0) + 1
    rows.append(row)
cols = ['mpm_id', 'organisation', 'name', 'country', 'registration_number', 'registered_address', 'year_founded',
        'parent_group', 'sources_origin', 'sources_control']
with open(sys.argv[2], 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
print('passports:', len(rows), 'facts:', counts)
print('Register shows another current legal name (not used; check for a rename):', len(renamed))
for m in renamed:
    print('  ', m['mpm_id'], m['name'], '|', m['legal_name'], '->', m['gleif_legal_name'], m['lei'])
print('GLEIF lists as INACTIVE (check for closure):', len(inactive))
for m in inactive:
    print('  ', m['mpm_id'], m['name'], m['country'], m['gleif_legal_name'], m['lei'])
