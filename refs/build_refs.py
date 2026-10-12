# -*- coding: utf-8 -*-
"""Harvest every reference of the manuscript from Crossref by DOI (title, authors, journal, volume, issue, pages, year) and
write refs.json. Each record was checked against the title/authors/year/journal before its DOI was added to DOIS."""
import json, re, urllib.request, urllib.parse, html

DOIS = [
 # field context: utility mapping, GPR
 "10.1016/j.tust.2007.04.002", "10.1016/j.tust.2007.06.001", "10.1016/j.tust.2011.10.011", "10.1016/j.tust.2012.11.007",
 "10.1016/j.tust.2022.104402", "10.1016/j.ndteint.2017.04.002", "10.3390/s16111827", "10.1109/tgrs.2016.2592679",
 "10.1016/j.jappgeo.2008.07.006", "10.1680/muen.14.00035", "10.1680/jinam.17.00033", "10.1680/muen.2010.163.1.3",
 "10.1016/j.trip.2025.101539", "10.1061/9780784406458", "10.1016/0926-9851(95)90033-0", "10.1016/b978-0-444-53348-7.00001-6",
 # fusion
 "10.1016/s1566-2535(02)00071-4", "10.1016/s0031-3203(02)00251-0", "10.1109/icgpr.2012.6254983",
 # method / evaluation
 "10.1109/2.30720", "10.1109/tit.1970.1054406", "10.1175/1520-0493(1950)078<0001:vofeit>2.0.co;2",
 "10.1175/1520-0450(1973)012<0595:anvpot>2.0.co;2", "10.1198/016214506000001437", "10.1111/j.1467-9868.2007.00587.x",
 "10.1145/1102351.1102430", "10.1609/aaai.v29i1.9602", "10.1145/775047.775151", "10.1111/j.1751-5823.2001.tb00465.x",
 "10.1023/a:1007413511361", "10.1016/j.patrec.2005.10.010", "10.1371/journal.pone.0118432",
 # software
 "10.1038/s41586-020-2649-2", "10.1038/s41592-019-0686-2", "10.1109/mcse.2007.55",
 # v1.1 additions: statistics, decision theory, partial observations
 "10.1214/aos/1176344552", "10.1111/j.1467-9868.2007.00593.x", "10.1214/ss/1009213286", "10.1093/biomet/26.4.404", "10.1109/tssc.1966.300074", "10.1016/j.autcon.2020.103229",
]

def get(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={"User-Agent": "SubSurface-refs/1.0 (mailto:suneritz@gmail.com)"})
    return json.load(urllib.request.urlopen(req, timeout=60))["message"]

out = []
for d in DOIS:
    m = get(d)
    au = [(a.get("family", a.get("name", "")), a.get("given", "")) for a in m.get("author", [])]
    ct = (m.get("container-title") or [""])[0]
    out.append(dict(doi=m["DOI"], title=html.unescape(re.sub(r"<[^>]+>", "", (m.get("title") or [""])[0])).strip(), authors=au,
                    journal=html.unescape(ct), year=(m.get("issued", {}).get("date-parts", [[None]])[0] or [None])[0],
                    volume=m.get("volume", ""), issue=m.get("issue", ""), pages=m.get("page", m.get("article-number", "")), type=m.get("type")))
json.dump(out, open("refs.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for r in out:
    print("%-34s %-5s %s | %s | %s %s" % (r["doi"][:34], r["year"], "; ".join(a[0] for a in r["authors"][:3]) or "(no authors)", r["title"][:70], r["journal"][:30], r["volume"]))
