"""Turn enrich/gleif-matches.csv into one feed file that fills only empty fields.

usage: gleif_to_feed.py enrich/gleif-matches.csv batches/<out>.csv
- only unambiguous matches of entities GLEIF lists as ACTIVE;
- lapsed LEI records give only the registration number and founding year
  (an address or parent may have changed since);
- only fields that are empty on the site (the 'missing' column);
- each layer's existing sources are kept and the GLEIF record is added, because
  the importer replaces a layer's source list with what the file gives.
Prints what it would fill and lists INACTIVE entities for a closure check.
"""
import csv, gzip, json, sys, datetime

R = '/home/claude/source-passports-data'
today = datetime.date.today().isoformat()
snap = json.load(gzip.open(R + '/mirror/passports-latest.json.gz'))
src = {p['id']: {L: v.get('sources') or [] for L, v in p['layers'].items()} for p in snap['passports']}
LIVE = {'ISSUED', 'PENDING_TRANSFER', 'PENDING_ARCHIVAL'}
rows, inactive, counts = [], [], {}
for m in csv.DictReader(open(sys.argv[1], encoding='utf-8')):
    if m['result'] != 'match':
        continue
    if m['entity_status'] != 'ACTIVE':
        inactive.append(m)
        continue
    miss = set(m['missing'].split())
    live = m['registration_status'] in LIVE
    vals = {}
    if 'registration_number' in miss and m['registered_as'].strip():
        vals['registration_number'] = m['registered_as'].strip()
    if 'year_founded' in miss and m['creation_date'][:4].isdigit():
        vals['year_founded'] = m['creation_date'][:4]
    if live and 'registered_address' in miss and m['legal_address'].strip():
        vals['registered_address'] = m['legal_address'].strip()
    if live and 'parent_group' in miss and m['parent_name'].strip():
        vals['parent_group'] = m['parent_name'].strip() + ' (direct parent recorded in the GLEIF LEI register)'
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
print('GLEIF lists as INACTIVE (check for closure):', len(inactive))
for m in inactive:
    print('  ', m['mpm_id'], m['name'], m['country'], m['gleif_legal_name'], m['lei'])
