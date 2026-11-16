#!/usr/bin/env python3
"""arXiv title search -> prints top hits; raw saved to arxiv/search_<slug>.xml. usage: arxiv_title.py 'title words' [slug]"""
import sys,re,urllib.request,urllib.parse,os,time,datetime,json
HERE=os.path.dirname(os.path.abspath(__file__))
q=sys.argv[1]; slug=sys.argv[2] if len(sys.argv)>2 else re.sub(r'\W+','_',q)[:40]
url="http://export.arxiv.org/api/query?max_results=4&search_query="+urllib.parse.quote(f'all:{q}' if '"' not in q else q)
for i in range(3):
    try: t=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"SBG-lit/1.0"}),timeout=40).read().decode(); break
    except Exception as e: t=''; time.sleep(3)
open(os.path.join(HERE,'arxiv',f'search_{slug}.xml'),'w').write(t)
open(os.path.join(HERE,'fetchlog.jsonl'),'a').write(json.dumps({"url":url,"out":f"arxiv/search_{slug}.xml","utc":datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})+"\n")
for e in re.findall(r'<entry>(.*?)</entry>',t,re.S):
    print(re.search(r'<id>http://arxiv.org/abs/(.*?)</id>',e).group(1),'|',re.search(r'<published>(.*?)</published>',e).group(1)[:10],'|',re.sub(r'\s+',' ',re.search(r'<title>(.*?)</title>',e,re.S).group(1))[:100],'|',', '.join(re.findall(r'<name>(.*?)</name>',e))[:60])
print('--')
time.sleep(3)
