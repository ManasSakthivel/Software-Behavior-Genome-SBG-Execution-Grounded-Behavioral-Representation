#!/usr/bin/env python3
import sys,re,urllib.request,urllib.parse,html
q=sys.argv[1]
req=urllib.request.Request("https://html.duckduckgo.com/html/?q="+urllib.parse.quote(q),headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/120.0"})
try: t=urllib.request.urlopen(req,timeout=30).read().decode('utf8','ignore')
except Exception as e: print('ERR',e); sys.exit()
for m in re.finditer(r'class="result__a" href="([^"]+)"[^>]*>(.*?)</a>',t,re.S):
    u=m.group(1); mm=re.search(r'uddg=([^&]+)',u); u=urllib.parse.unquote(mm.group(1)) if mm else u
    print(re.sub('<.*?>','',html.unescape(m.group(2)))[:90],'|',u)
