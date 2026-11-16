#!/usr/bin/env python3
"""P03: download two SMALL public datasets (<5 MB total) that feed the feasibility check.
 - Refactory data.zip (githubhuyang/refactory, 1.9 MB, LGPL-3.0 repo licence)
 - HumanEvalPack python via HF datasets-server JSON rows (164 rows, MIT)
Records sha256 + sizes to data/P03_downloads.json."""
import urllib.request, json, hashlib, datetime, os
rec={"utc":datetime.datetime.utcnow().isoformat()+"Z","files":[]}
def dl(u,p):
    r=urllib.request.Request(u,headers={"User-Agent":"wpd-d3"}); b=urllib.request.urlopen(r,timeout=60).read()
    open(p,"wb").write(b); rec["files"].append({"url":u,"path":p,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()}); return b
dl("https://github.com/githubhuyang/refactory/raw/master/data.zip","data/refactory_data.zip")
rows=[]
for off in (0,100):
    b=dl(f"https://datasets-server.huggingface.co/rows?dataset=bigcode/humanevalpack&config=python&split=test&offset={off}&length=100",f"data/hep_rows_{off}.json")
    rows+= [x["row"] for x in json.loads(b)["rows"]]
json.dump(rows,open("data/humanevalpack_python.json","w"))
b=open("data/humanevalpack_python.json","rb").read()
rec["files"].append({"url":"(merged)","path":"data/humanevalpack_python.json","bytes":len(b),"sha256":hashlib.sha256(b).hexdigest(),"n_rows":len(rows)})
json.dump(rec,open("data/P03_downloads.json","w"),indent=1); print(json.dumps(rec,indent=1))
