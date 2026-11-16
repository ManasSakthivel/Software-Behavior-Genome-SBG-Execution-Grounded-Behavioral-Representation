#!/usr/bin/env python3
"""P02: fetch arXiv titles/abstracts for candidate datasets (public metadata only). Output P02_arxiv.json; titles are printed so IDs are verified, not assumed."""
import json, urllib.request, urllib.parse, re, datetime, xml.etree.ElementTree as ET
ns={'a':'http://www.w3.org/2005/Atom'}
def q(url):
    r=urllib.request.Request(url,headers={"User-Agent":"wpd-d3"})
    return ET.fromstring(urllib.request.urlopen(r,timeout=20).read())
res={"fetched_utc":datetime.datetime.utcnow().isoformat()+"Z","by_id":{}, "by_title":{}}
ids=["1905.13334","2105.12787","2308.07124","2105.12655","2203.07814","1903.06725","2402.02961","2102.04664","2108.07732"]
root=q("http://export.arxiv.org/api/query?max_results=20&id_list="+",".join(ids))
for e in root.findall('a:entry',ns):
    i=e.find('a:id',ns).text.split('/abs/')[-1]
    res["by_id"][i]={"title":" ".join(e.find('a:title',ns).text.split()),"summary":" ".join(e.find('a:summary',ns).text.split())}
titles={"typebugs":"TypeBugs python type errors benchmark","defects4py":"Defects4Py","refactory":"Re-factoring based program repair applied to programming assignments",
        "mutation_py":"mutation testing Python MutPy cosmic-ray mutants equivalent","pyref":"PyRef refactoring detection Python","debugbench":"DebugBench evaluating debugging capability of large language models",
        "codeflaws":"Codeflaws programming competition benchmark automated program repair","codenet_py_clone":"semantic code clone detection Codeforces solutions Python equivalent programs"}
for k,t in titles.items():
    root=q("http://export.arxiv.org/api/query?max_results=3&search_query="+urllib.parse.quote('all:"'+t+'"' if k in("refactory",) else 'all:'+t.replace(' ','+')))
    res["by_title"][k]=[{"id":e.find('a:id',ns).text.split('/abs/')[-1],"title":" ".join(e.find('a:title',ns).text.split()),"summary":" ".join(e.find('a:summary',ns).text.split())[:700]} for e in root.findall('a:entry',ns)]
json.dump(res,open("P02_arxiv.json","w"),indent=1)
for i,v in res["by_id"].items(): print(i,"|",v["title"])
for k,l in res["by_title"].items():
    for v in l: print(k,"->",v["id"],"|",v["title"][:100])
