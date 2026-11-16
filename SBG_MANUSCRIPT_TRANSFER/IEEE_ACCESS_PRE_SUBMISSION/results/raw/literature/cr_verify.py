#!/usr/bin/env python3
"""Crossref verification helper (stdlib). Usage: cr_verify.py LISTFILE
LISTFILE lines: key<TAB>10.xxxx/doi   OR   key<TAB>q:free text bibliographic query
Writes crossref/<key>.json (raw) and appends a normalised record to crossref_verified.jsonl
Query mode stores the top-3 candidates and uses the top-1 only as a CANDIDATE (needs human title check)."""
import sys, json, os, time, urllib.request, urllib.parse, urllib.error, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "SBG-literature-check/1.0 (mailto:reviewer@example.org)"}

def get(url):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 404, b""
            time.sleep(2 + i * 3)
        except Exception:
            time.sleep(2 + i * 3)
    return None, b""

def norm(m):
    iss = (m.get("issued") or {}).get("date-parts", [[None]])[0]
    return {
        "doi": m.get("DOI"), "title": (m.get("title") or [""])[0],
        "authors": [f"{a.get('given','')} {a.get('family','')}".strip() for a in m.get("author", [])],
        "container": (m.get("container-title") or [""])[0], "year": iss[0] if iss else None,
        "pages": m.get("page"), "type": m.get("type"), "volume": m.get("volume"),
        "article_number": m.get("article-number"),
    }

utc = lambda: datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
os.makedirs(os.path.join(HERE, "crossref"), exist_ok=True)
for line in open(sys.argv[1]):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    key, what = line.split("\t", 1)
    if what.startswith("q:"):
        url = "https://api.crossref.org/works?rows=3&query.bibliographic=" + urllib.parse.quote(what[2:])
        st, data = get(url)
        raw = json.loads(data) if data else {}
        items = raw.get("message", {}).get("items", [])
        rec = {"key": key, "mode": "query", "query": what[2:], "status": st, "fetched_utc": utc(),
               "candidates": [norm(i) for i in items]}
    else:
        url = "https://api.crossref.org/works/" + urllib.parse.quote(what, safe="/")
        st, data = get(url)
        raw = json.loads(data) if data else {}
        rec = {"key": key, "mode": "doi", "doi_requested": what, "status": st, "fetched_utc": utc(),
               "record": norm(raw["message"]) if st == 200 and "message" in raw else None}
    with open(os.path.join(HERE, "crossref", key + ".json"), "w") as f:
        json.dump(raw, f)
    with open(os.path.join(HERE, "crossref_verified.jsonl"), "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    if rec["mode"] == "doi":
        r = rec["record"]
        print(f"{key:28s} {st} | {r and r['year']} | {r and r['title'][:80]} | {r and (r['authors'][:2])} | {r and r['container'][:50]}")
    else:
        for c in rec["candidates"][:2]:
            print(f"{key:28s} Q {st} | {c['year']} | {c['title'][:80]} | {c['authors'][:2]} | {c['container'][:50]} | {c['doi']}")
    time.sleep(0.4)
