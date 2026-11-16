#!/bin/bash
# usage: getarxiv.sh <arxiv-id> <short-name>   -> arxiv/<name>.xml (API metadata), pdf/<name>.pdf, text/<name>.txt
cd "$(dirname "$0")"
python3 fetch.py "http://export.arxiv.org/api/query?id_list=$1" arxiv/$2.xml >/dev/null
python3 fetch.py "https://arxiv.org/pdf/$1" pdf/$2.pdf
python3 pdf2txt.py pdf/$2.pdf text/$2.txt
python3 - <<P
import re
t=open('arxiv/$2.xml').read()
e=re.search(r'<entry>(.*?)</entry>',t,re.S).group(1)
print('TITLE:',re.sub(r'\s+',' ',re.search(r'<title>(.*?)</title>',e,re.S).group(1)))
print('AUTHORS:',', '.join(re.findall(r'<name>(.*?)</name>',e)))
print('PUBLISHED:',re.search(r'<published>(.*?)</published>',e).group(1)[:10])
jr=re.search(r'<arxiv:journal_ref[^>]*>(.*?)</arxiv:journal_ref>',e,re.S); print('JREF:',jr.group(1) if jr else None)
d=re.search(r'<arxiv:doi[^>]*>(.*?)</arxiv:doi>',e); print('DOI:',d.group(1) if d else None)
P
