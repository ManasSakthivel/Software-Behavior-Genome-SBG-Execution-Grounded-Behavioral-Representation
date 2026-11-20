#!/usr/bin/env python3
"""Copy ONLY cited entries from research/literature/VERIFIED_REFERENCES.bib into references.bib."""
import re, pathlib
P = pathlib.Path(__file__).resolve().parent.parent
src = (P.parent.parent / "research/literature/VERIFIED_REFERENCES.bib").read_text()
keys = set()
for f in [P / "main.tex", *P.glob("sections/*.tex"), *P.glob("tables/*.tex")]:
    for m in re.finditer(r"\\cite\w*\{([^}]*)\}", f.read_text()):
        keys |= {k.strip() for k in m.group(1).split(",")}
entries = {m.group(1): m.group(0) for m in re.finditer(r"@\w+\{([^,\s]+),.*?\n\}\n", src, re.S)}
missing = sorted(keys - entries.keys())
assert not missing, f"cited but not in VERIFIED_REFERENCES.bib: {missing}"
(P / "references.bib").write_text("\n".join(entries[k] for k in sorted(keys)))
print(len(keys), "entries written")
