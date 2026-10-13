import json, urllib.request, urllib.parse
refs=json.load(open('refs.json',encoding='utf-8'))
dois=[r['doi'] for r in refs]+["10.5281/zenodo.23308158","10.5281/zenodo.23306880","10.5281/zenodo.23306882","10.5281/zenodo.21223570"]
bad=[]
for d in dois:
    try:
        r=json.load(urllib.request.urlopen("https://doi.org/api/handles/"+urllib.parse.quote(d,safe="/()<>:;"),timeout=30))
        ok=r.get("responseCode")==1
    except Exception as e:
        ok=False
    if not ok: bad.append(d)
print(len(dois),"checked; unresolved:",bad)
