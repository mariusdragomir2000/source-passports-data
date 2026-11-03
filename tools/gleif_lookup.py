"""Look up passports in the GLEIF LEI register (open data, CC0) by their exact legal name.

Runs in GitHub Actions (the register API is public; no key). For every published
passport that has a legal name but is missing a registration number, registered
address, founding year or parent group, it asks GLEIF for records with that legal
name in that country and keeps only an unambiguous match: exactly one record whose
normalised legal name equals the passport's and whose legal address or jurisdiction
is in the passport's country. Writes enrich/gleif-matches.csv for review; it changes
nothing on the site by itself.
"""
import csv, gzip, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request

API = 'https://api.gleif.org/api/v1'
UA = 'source-passports-enrich/1.0 (+https://github.com/mariusdragomir2000/source-passports-data)'
WANT = ['registration_number', 'registered_address', 'year_founded', 'parent_group']
FORMS = {'limited': 'ltd', 'incorporated': 'inc', 'corporation': 'corp', 'company': 'co',
         'public limited company': 'plc', 'societe anonyme': 'sa', 'aktiengesellschaft': 'ag',
         'gesellschaft mit beschrankter haftung': 'gmbh'}
last = [0.0]


def get(path, params=None):
    """GET a GLEIF API path, at most one request per 1.1 s (limit is 60 a minute)."""
    url = API + path + ('?' + urllib.parse.urlencode(params) if params else '')
    for attempt in range(4):
        wait = 1.1 - (time.time() - last[0])
        if wait > 0:
            time.sleep(wait)
        last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/vnd.api+json'})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429 or e.code >= 500:
                time.sleep(30 * (attempt + 1))
                continue
            raise
        except Exception:
            time.sleep(30 * (attempt + 1))
    return None


def norm(name):
    s = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'\([^)]*\)', ' ', s)
    s = re.sub(r'[^a-z0-9 ]+', ' ', s)
    s = ' '.join(s.split())
    for long, short in FORMS.items():
        s = re.sub(r'\b' + long + r'\b', short, s)
    return s


def has(fv):
    if not fv:
        return False
    if fv.get('access') == 'on_request':
        return fv.get('status') not in ('not_disclosed', '', None)
    v = fv.get('value')
    return bool(v) if not isinstance(v, str) else v.strip() != ''


def address(a):
    if not a:
        return ''
    parts = [', '.join(x for x in a.get('addressLines') or [] if x)]
    city = ' '.join(x for x in [a.get('postalCode'), a.get('city')] if x)
    parts += [city, a.get('country') or '']
    return ', '.join(p for p in parts if p)


def main(snapshot, out):
    snap = json.load(gzip.open(snapshot))
    todo = []
    for p in snap['passports']:
        if p.get('record_status', 'active') != 'active':
            continue
        f = {k: v for L in p['layers'].values() for k, v in L['fields'].items()}
        if f['entity_type']['value'] == 'political_party':
            continue
        ln = (f.get('legal_name') or {}).get('value') or ''
        if not ln.strip():
            continue
        missing = [k for k in WANT if k in f and not has(f[k])]
        if missing:
            todo.append((p['id'], p['name'], f['country']['value'], ln.strip(), missing))
    print('passports to look up:', len(todo), flush=True)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cols = ['mpm_id', 'name', 'country', 'legal_name', 'missing', 'result', 'lei', 'gleif_legal_name',
            'registration_status', 'entity_status', 'registered_as', 'registration_authority',
            'legal_address', 'creation_date', 'parent_lei', 'parent_name', 'last_update']
    with open(out, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for i, (mid, name, cc, ln, missing) in enumerate(todo):
            row = {'mpm_id': mid, 'name': name, 'country': cc, 'legal_name': ln, 'missing': ' '.join(missing)}
            target = norm(ln)
            found = {}
            queries = [{'filter[entity.legalName]': re.sub(r'\s*\([^)]*\)', '', ln).strip()},
                       {'filter[fulltext]': re.sub(r'\s*\([^)]*\)', '', ln).strip(), 'filter[entity.legalAddress.country]': cc}]
            for q in queries:
                q['page[size]'] = '20'
                d = get('/lei-records', q) or {}
                for rec in d.get('data', []):
                    e = rec['attributes']['entity']
                    names = [e.get('legalName', {}).get('name', '')] + [o.get('name', '') for o in e.get('otherNames') or []]
                    inside = (e.get('legalAddress') or {}).get('country') == cc or (e.get('jurisdiction') or '').upper().startswith(cc)
                    if inside and any(norm(n) == target for n in names if n):
                        found[rec['id']] = rec
                if found:
                    break
            if len(found) != 1:
                row['result'] = 'none' if not found else 'ambiguous'
                w.writerow(row)
                continue
            rec = next(iter(found.values()))
            a = rec['attributes']; e = a['entity']; reg = a['registration']
            row.update({'result': 'match', 'lei': rec['id'], 'gleif_legal_name': e.get('legalName', {}).get('name', ''),
                        'registration_status': reg.get('status', ''), 'entity_status': e.get('status', ''),
                        'registered_as': e.get('registeredAs') or '', 'registration_authority': (e.get('registeredAt') or {}).get('id') or '',
                        'legal_address': address(e.get('legalAddress')), 'creation_date': e.get('creationDate') or '',
                        'last_update': reg.get('lastUpdateDate', '')})
            if 'parent_group' in missing:
                par = get('/lei-records/%s/direct-parent' % rec['id'])
                if par and par.get('data'):
                    row['parent_lei'] = par['data']['id']
                    row['parent_name'] = par['data']['attributes']['entity'].get('legalName', {}).get('name', '')
            w.writerow(row)
            if i % 100 == 0:
                fh.flush()
                print(i, 'done', flush=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
