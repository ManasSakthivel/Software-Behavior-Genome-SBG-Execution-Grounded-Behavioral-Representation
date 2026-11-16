#!/usr/bin/env python3
"""Semantic Scholar paper metadata + OA pdf for list of ids. usage: s2_meta.py id [id...]  (ids like DOI:..., ARXIV:...)"""
import sys,json,time,urllib.request,urllib.error,os,datetime
HERE=os.path.dirname(os.path.abspath(__file__))
F="title,authors,year,venue,externalIds,citationCount,openAccessPdf,isOpenAccess,publicationVenue"
for pid in sys.argv[1:]:
    url=f"https://api.semanticscholar.org/graph/v1/paper/{pid}?fields={F}"
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"SBG-lit/1.0"}),timeout=40) as r:
                d=json.loads(r.read()); break
        except urllib.error.HTTPError as e:
            d={"error":e.code}; 
            if e.code==429: time.sleep(5+5*i); continue
            break
        except Exception as e: d={"error":str(e)}; time.sleep(3)
    d["_fetched_utc"]=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"); d["_query_id"]=pid
    open(os.path.join(HERE,"s2_meta.jsonl"),"a").write(json.dumps(d,ensure_ascii=False)+"\n")
    oa=(d.get("openAccessPdf") or {}).get("url")
    print(pid[:45].ljust(46),d.get("year"),"|",(d.get("title") or str(d.get("error")))[:60],"| cites",d.get("citationCount"),"| OA:",oa)
    time.sleep(1.5)
