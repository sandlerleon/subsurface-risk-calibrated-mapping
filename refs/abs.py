import json, urllib.request, urllib.parse, re, html
for doi in ["10.3390/s16111827","10.1016/j.autcon.2020.103229","10.1016/s1566-2535(02)00071-4","10.1109/icgpr.2012.6254983","10.1016/s0031-3203(02)00251-0","10.1016/j.tust.2012.11.007","10.1016/j.tust.2022.104402","10.1016/j.tust.2007.04.002"]:
    req=urllib.request.Request("https://api.crossref.org/works/"+urllib.parse.quote(doi),headers={"User-Agent":"refs/1.0 (mailto:suneritz@gmail.com)"})
    m=json.load(urllib.request.urlopen(req,timeout=60))["message"]
    a=m.get("abstract","")
    print(doi,"|",html.unescape(re.sub(r"<[^>]+>","",a))[:900] or "(no abstract in Crossref)")
    print()
