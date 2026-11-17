#!/usr/bin/env python3
"""Checks: (1) every \\cite key is in references.bib (and bib has only cited keys), (2) every \\ref/\\label resolves,
(3) every \\input/\\includegraphics/\\dotfig file exists, (4) every number in generated results tables appears in
its cited source file (tables/SOURCES.json). Exit code 1 on any failure."""
import re, json, pathlib, sys
P = pathlib.Path(__file__).resolve().parent.parent
ROOT = P.parent.parent
files = [P / "main.tex", *sorted(P.glob("sections/*.tex")), *sorted(P.glob("tables/*.tex"))]
text = {f: f.read_text() for f in files}
all_ = "\n".join(text.values())
bad = []

cites = {k.strip() for m in re.finditer(r"\\cite\w*\{([^}]*)\}", all_) for k in m.group(1).split(",")}
bib = set(re.findall(r"@\w+\{([^,\s]+),", (P / "references.bib").read_text()))
bad += [f"cite key not in references.bib: {k}" for k in sorted(cites - bib)]
bad += [f"references.bib entry never cited: {k}" for k in sorted(bib - cites)]

labels = set(re.findall(r"\\label\{([^}]*)\}", all_))
# \dotfig{name}{caption}{label} defines a label via the macro
labels |= set(re.findall(r"\\dotfig\{[^}]*\}\{(?:[^{}]|\{[^{}]*\})*\}\{([^}]*)\}", all_))
refs = {k.strip() for m in re.finditer(r"\\(?:ref|eqref|autoref|pageref)\{([^}]*)\}", all_) for k in m.group(1).split(",")}
refs |= {k for m in re.finditer(r"\\ref\{([^}]*)\}", all_) for k in [m.group(1)]}
bad += [f"unresolved ref: {k}" for k in sorted(refs - labels)]
# refs written as Fig.~\ref{fig:a}, \ref{fig:b} are covered by the pattern above (bare \ref)
for m in re.finditer(r"Fig\.~\\ref\{[^}]*\}(?:,\s*\\ref\{[^}]*\})+", all_):
    pass

for f, t in text.items():
    for m in re.finditer(r"\\input\{([^}]*)\}", t):
        p = P / (m.group(1) if m.group(1).endswith(".tex") else m.group(1) + ".tex")
        if not p.exists(): bad.append(f"{f.name}: missing input {m.group(1)}")
    for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", t):
        if "#1" in m.group(1): continue
        if not (P / m.group(1)).resolve().exists(): bad.append(f"{f.name}: missing graphic {m.group(1)}")
    for m in re.finditer(r"\\dotfig\{([^}]*)\}", t):
        if not (P / "figures" / (m.group(1) + ".dot")).exists(): bad.append(f"{f.name}: missing figures/{m.group(1)}.dot")
    for m in re.finditer(r"\\path\{((?:results|research|paper|docs|reports)/[^}]*)\}", t):
        if not (ROOT / m.group(1)).exists(): bad.append(f"{f.name}: cited path does not exist: {m.group(1)}")

NUM = re.compile(r"-?\d+(?:\.\d+)?(?:[eE]-?\d+)?")
def source_numbers(p):
    return {m.group(0) for m in NUM.finditer((ROOT / p).read_text())}
def present(tok, vals):
    d = len(tok.split(".")[1]) if "." in tok else 0
    for v in vals:
        try:
            x = float(v)
        except ValueError:
            continue
        if f"{x:.{d}f}" == tok or f"{abs(x):.{d}f}" == tok.lstrip("-"):
            return True
    return False
n_checked = 0
for tname, srcs in json.load(open(P / "tables/SOURCES.json")).items():
    body = (P / "tables" / f"{tname}.tex").read_text().split("\\hline")[2:]  # skip header
    body = "\n".join(body)
    vals = set().union(*(source_numbers(s) for s in srcs)) if srcs else set()
    for tok in re.findall(r"(?<![A-Za-z_\\\-+\d.])-?\d+(?:\.\d+)?(?![A-Za-z_\d])", body):
        n_checked += 1
        if not present(tok, vals): bad.append(f"table {tname}: number {tok} not found in {srcs}")
print(f"cites={len(cites)} bib={len(bib)} labels={len(labels)} refs={len(refs)} table_numbers_checked={n_checked}")
print("\n".join(bad) if bad else "ALL CHECKS PASSED")
sys.exit(1 if bad else 0)
