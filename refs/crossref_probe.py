import json, sys, urllib.parse, urllib.request
qs = [l.strip() for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
for q in qs:
    url = "https://api.crossref.org/works?rows=4&select=DOI,title,author,issued,container-title,volume,page,type&query.bibliographic=" + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={"User-Agent": "SubSurface-refs/1.0 (mailto:suneritz@gmail.com)"})
    try:
        items = json.load(urllib.request.urlopen(req, timeout=60))["message"]["items"]
    except Exception as e:
        print("ERR", q, e); continue
    print("##", q)
    for it in items:
        au = ", ".join(a.get("family", "?") for a in it.get("author", [])[:3])
        print("  %s | %s | %s | %s %s | %s" % ((it.get("title") or ["?"])[0][:90], au, it.get("issued", {}).get("date-parts", [[None]])[0][0], (it.get("container-title") or ["?"])[0][:40], it.get("volume", ""), it["DOI"]))
