#!/usr/bin/env python3
"""OpenAlex forward citations. usage: fwd.py label DOI  -> openalex/fwd_<label>.json (id,title,year,venue,doi,cited_by)"""
import sys,json,urllib.request,os,time,datetime,urllib.parse
HERE=os.path.dirname(os.path.abspath(__file__))
UA={"User-Agent":"SBG-lit/1.0 (mailto:reviewer@example.org)"}
def g(u):
    for i in range(3):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40).read())
        except Exception as e: time.sleep(2+i*2); err=e
    return {"error":str(err)}
label,ident=sys.argv[1],sys.argv[2]
if ident.startswith("W"): wid=ident
else:
    d=g(f"https://api.openalex.org/works/doi:{ident}?select=id,title,cited_by_count"); wid=d.get("id","").split("/")[-1]
out=[];page=1
while True:
    d=g(f"https://api.openalex.org/works?filter=cites:{wid}&per-page=100&page={page}&select=id,doi,title,publication_year,cited_by_count,primary_location,type")
    r=d.get("results",[])
    for w in r:
        out.append({"id":w["id"],"doi":w.get("doi"),"title":w.get("title"),"year":w.get("publication_year"),"venue":((w.get("primary_location") or {}).get("source") or {}).get("display_name"),"cited_by":w.get("cited_by_count")})
    if len(r)<100 or page>=4: break
    page+=1
json.dump({"label":label,"openalex_id":wid,"fetched_utc":datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),"n":len(out),"citers":out},open(os.path.join(HERE,f"openalex/fwd_{label}.json"),"w"),indent=1)
print(label,wid,len(out))
