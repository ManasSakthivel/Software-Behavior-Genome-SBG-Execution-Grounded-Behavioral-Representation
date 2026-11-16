#!/usr/bin/env python3
"""OpenAlex keyword search -> openalex/search_<slug>.json ; prints top hits. usage: oa_search.py 'query' slug [from_year]"""
import sys,json,urllib.request,urllib.parse,os,time,datetime
HERE=os.path.dirname(os.path.abspath(__file__))
q,slug=sys.argv[1],sys.argv[2]; fy=sys.argv[3] if len(sys.argv)>3 else "2018"
u="https://api.openalex.org/works?search="+urllib.parse.quote(q)+f"&filter=from_publication_date:{fy}-01-01&per-page=12&select=id,doi,title,publication_year,cited_by_count,primary_location,type"
d=None
for i in range(4):
    try: d=json.loads(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"SBG-lit/1.0 (mailto:reviewer@example.org)"}),timeout=40).read()); break
    except Exception as e: time.sleep(4+3*i)
d=d or {"results":[]}
json.dump({"query":q,"url":u,"fetched_utc":datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),"results":d["results"]},open(os.path.join(HERE,f"openalex/search_{slug}.json"),"w"),indent=1)
print("\n##",q)
for w in d["results"]: print(w["publication_year"],"|",(w["title"] or "")[:95],"|",((w.get("primary_location") or {}).get("source") or {}).get("display_name","")[:28] if (w.get("primary_location") or {}).get("source") else "","|",w.get("doi"))
time.sleep(1.5)
