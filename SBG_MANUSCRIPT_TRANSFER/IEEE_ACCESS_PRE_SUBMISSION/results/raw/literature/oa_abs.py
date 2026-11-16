#!/usr/bin/env python3
"""OpenAlex abstract/OA-location collector. usage: oa_abs.py DOI [DOI...] ; appends to openalex_abstracts.jsonl"""
import sys,json,time,urllib.request,urllib.error,os,datetime
HERE=os.path.dirname(os.path.abspath(__file__))
def inv(ii):
    if not ii: return None
    w=[]; 
    for k,v in ii.items():
        for p in v: w.append((p,k))
    return ' '.join(k for p,k in sorted(w))
for doi in sys.argv[1:]:
    url=f"https://api.openalex.org/works/doi:{doi}?select=id,doi,title,publication_year,cited_by_count,abstract_inverted_index,open_access,best_oa_location,locations,authorships,primary_location"
    try:
        d=json.loads(urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"SBG-lit/1.0"}),timeout=40).read())
    except Exception as e:
        print(doi,'ERR',e); continue
    rec={"doi":doi,"openalex_id":d.get("id"),"title":d.get("title"),"year":d.get("publication_year"),"cited_by":d.get("cited_by_count"),
         "abstract":inv(d.get("abstract_inverted_index")),"is_oa":(d.get("open_access") or {}).get("is_oa"),
         "oa_urls":[(l.get("landing_page_url"),l.get("pdf_url")) for l in d.get("locations",[]) if l.get("is_oa")],
         "fetched_utc":datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    open(os.path.join(HERE,"openalex_abstracts.jsonl"),"a").write(json.dumps(rec,ensure_ascii=False)+"\n")
    print(doi,'|',rec['year'],'|',(rec['title'] or '')[:50],'| cited',rec['cited_by'],'| abs',bool(rec['abstract']),'| OA',rec['oa_urls'][:2])
    time.sleep(0.5)
