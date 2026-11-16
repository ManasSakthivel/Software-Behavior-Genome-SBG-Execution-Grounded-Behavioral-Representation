#!/usr/bin/env python3
"""Tiny logged fetcher (stdlib only). Usage: fetch.py URL OUTFILE
Appends one JSON line to fetchlog.jsonl (url, out, http status, bytes, UTC time)."""
import sys, json, time, urllib.request, urllib.error, os, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
url, out = sys.argv[1], sys.argv[2]
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (SBG-literature-check; academic, non-commercial)", "Accept": "*/*"})
status, data, err = None, b"", None
for _try in range(4):
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            status = r.status
            data = r.read()
        err = None
        break
    except urllib.error.HTTPError as e:
        status, err = e.code, str(e)
        try: data = e.read()
        except Exception: pass
        if e.code in (429, 500, 502, 503): time.sleep(5 * (_try + 1)); continue
        break
    except Exception as e:
        err = repr(e); time.sleep(4 * (_try + 1))
os.makedirs(os.path.dirname(os.path.join(HERE, out)) or HERE, exist_ok=True)
with open(os.path.join(HERE, out), "wb") as f:
    f.write(data)
rec = {"url": url, "out": out, "status": status, "bytes": len(data), "err": err,
       "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
with open(os.path.join(HERE, "fetchlog.jsonl"), "a") as f:
    f.write(json.dumps(rec) + "\n")
print(status, len(data), url[:100])
