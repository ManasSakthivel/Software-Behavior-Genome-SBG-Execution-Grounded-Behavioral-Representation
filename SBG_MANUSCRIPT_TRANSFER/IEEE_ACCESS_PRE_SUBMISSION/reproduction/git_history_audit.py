#!/usr/bin/env python3
"""A2: prove (read-only git) which frozen/pinned files changed AFTER the commit that introduced their freeze file.
Output: PKG/results/raw/repro/git_history_audit.json / .md  (pure stdlib; only `git log` / `git show` / `git rev-list`)."""
import hashlib, json, pathlib, subprocess, sys
PKG = pathlib.Path(__file__).resolve().parents[1]
REPO = PKG.parent / "SBG"
OUT = PKG / "results" / "raw" / "repro"

def git(*a):
    r = subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)
    return r.stdout

def blob(c, p):
    r = subprocess.run(["git", "-C", str(REPO), "show", f"{c}:{p}"], capture_output=True)
    return hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None

def commits(path):
    # --follow only works for one path; also list renames
    return [l.split(" ", 2) for l in git("log", "--follow", "--format=%h %ad %s", "--date=iso-strict", "--", path).splitlines()]

def first_commit_of(path):
    cs = git("log", "--diff-filter=A", "--format=%h", "--", path).split()
    return cs[-1] if cs else None

def is_ancestor(a, b):
    return subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor", a, b]).returncode == 0

FREEZES = {
    "FREEZE_V8 (+AMEND1/2)": ("artifacts/final/FREEZE_V8.json", ["artifacts/final/FREEZE_V8.json", "artifacts/final/FREEZE_V8_AMENDMENT1.json", "artifacts/final/FREEZE_V8_AMENDMENT2.json"]),
    "FREEZE_V9": ("artifacts/final/FREEZE_V9.json", ["artifacts/final/FREEZE_V9.json"]),
    "FREEZE_V10": ("artifacts/final/FREEZE_V10.json", ["artifacts/final/FREEZE_V10.json", "artifacts/final/FREEZE_V10_SCORED.json"]),
}
res = {}
for name, (anchor, frs) in FREEZES.items():
    fc = first_commit_of(anchor)
    pins = set()
    for fr in frs:
        d = json.loads((REPO / fr).read_text())
        def walk(n):
            if isinstance(n, dict):
                for k, v in n.items():
                    if isinstance(v, str) and len(v) == 64 and "/" in k: pins.add(k)
                    if k in ("path", "file", "scored_file") and isinstance(v, str) and "/" in v and not v.startswith("/"): pins.add(v)
                    walk(v)
            elif isinstance(n, list):
                for x in n: walk(x)
        walk(d)
    pins |= set(frs)
    rows = []
    for p in sorted(pins):
        cs = commits(p)
        if not cs:
            rows.append(dict(path=p, status="untracked/no-history")); continue
        after = [c for c in cs if c[0] != fc and not is_ancestor(c[0], fc)]  # not ancestors of freeze commit => later
        same = [c for c in cs if c[0] == fc]
        rows.append(dict(path=p, n_commits=len(cs), first=cs[-1][0], last=cs[0][0], last_date=cs[0][1][:10],
                         in_freeze_commit=bool(same), commits_after_freeze_commit=[c[0] + " " + c[2][:70] for c in after],
                         blob_at_freeze=blob(fc, p), blob_HEAD=blob("HEAD", p)))
    res[name] = dict(anchor=anchor, freeze_commit=fc, n_paths=len(rows), rows=rows)
(OUT / "git_history_audit.json").write_text(json.dumps(res, indent=1))
lines = []
for n, r in res.items():
    lines.append(f"## {n}: freeze file introduced at {r['freeze_commit']} ({r['n_paths']} pinned paths)")
    chg = [x for x in r["rows"] if x.get("commits_after_freeze_commit")]
    lines.append(f"paths with later commits: {len(chg)}")
    for x in chg:
        lines.append(f"- {x['path']}: blob@freeze={str(x['blob_at_freeze'])[:12]} HEAD={str(x['blob_HEAD'])[:12]} later={x['commits_after_freeze_commit']}")
    lines.append("")
(OUT / "git_history_audit.md").write_text("\n".join(lines))
print("\n".join(lines))
