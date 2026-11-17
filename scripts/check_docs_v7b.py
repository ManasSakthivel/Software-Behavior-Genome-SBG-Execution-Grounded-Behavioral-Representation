#!/usr/bin/env python3
"""V7-B documentation check (does NOT replace the legacy V5 consistency gate, which validates docs/README_pre_v7b.md).
Checks README.md, REPRODUCIBILITY.md, datasets/README.md: relative links, referenced repo paths, documented commands
(make targets, python -m modules, scripts and their flags), README claims against implementation capabilities, and a
blacklist of unsupported claims. Exit 0 = all pass, 1 = failures. Lightweight: runs nothing expensive."""
import re, subprocess, sys, pathlib, json
ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ["README.md", "REPRODUCIBILITY.md", "datasets/README.md"]
fails = []
def fail(c, m): fails.append(f"[{c}] {m}")

texts = {d: (ROOT / d).read_text() for d in DOCS}
make_targets = set(re.findall(r"^([A-Za-z0-9_-]+):", (ROOT / "Makefile").read_text(), re.M))
run_eval = (ROOT / "scripts/run_evaluation.sh").read_text()

for d, t in texts.items():
    base = (ROOT / d).parent
    # 1 relative links
    for m in re.finditer(r"\]\(([^)#\s]+)(#[^)]*)?\)", t):
        u = m.group(1)
        if not u.startswith(("http", "mailto")) and not (base / u).exists(): fail("links", f"{d}: broken link {u}")
    # 2 referenced repo paths (backticked, no wildcards/placeholders)
    for m in re.finditer(r"`((?:scripts|sbgv7|tests|docs|research|reports|results|paper|experiments|examples|datasets|external)/[^\s`*<>{}$]+)`", t):
        p = m.group(1).rstrip(".,:;)")
        if (ROOT / p).exists() or p.startswith("results/repro"): continue  # results/repro is created by the script and gitignored
        if re.fullmatch(r"research/v7b-final-validation", p): continue  # branch name
        fail("paths", f"{d}: referenced path missing: {p}")
    # 3 documented commands
    for m in re.finditer(r"\bmake ([a-z][a-z0-9-]*)", t):
        if m.group(1) not in make_targets: fail("commands", f"{d}: make target '{m.group(1)}' not in Makefile")
    for m in re.finditer(r"python -m ([A-Za-z0-9_.]+)", t):
        mod = m.group(1)
        if mod in ("pytest",): continue
        if not (ROOT / (mod.replace(".", "/") + ".py")).exists() and not (ROOT / mod.replace(".", "/") / "__main__.py").exists() \
           and not (ROOT / mod.replace(".", "/") / "run.py").exists():
            fail("commands", f"{d}: python -m {mod} has no module file")
    for m in re.finditer(r"scripts/run_evaluation\.sh (--[a-z-]+)", t):
        if m.group(1) not in run_eval: fail("commands", f"{d}: run_evaluation.sh flag {m.group(1)} not implemented")
    for m in re.finditer(r"(?:\.venv/bin/python|python3?) ((?:scripts|experiments)/[\w/.-]+\.py)", t):
        if not (ROOT / m.group(1)).exists(): fail("commands", f"{d}: script {m.group(1)} missing")

# 4 README capability claims vs implementation
readme = texts["README.md"]
cfg_src = (ROOT / "sbgv7/config.py").read_text()
if "S3 is not implemented" not in cfg_src: fail("capabilities", "config no longer refuses S3 but README says not implemented")
verdicts_src = (ROOT / "sbgv7/records.py").read_text() + (ROOT / "sbgv7/decide.py").read_text()
for v in ("DIVERGENT_OBSERVABLE", "NO_DIVERGENCE_OBSERVED", "INSUFFICIENT"):
    if v not in verdicts_src: fail("capabilities", f"verdict {v} not found in sbgv7")
if re.search(r'"(EQUIVALENT|EQUAL|SAME_BEHAV\w*|VERIFIED|PROVEN\w*)"', verdicts_src): fail("capabilities", "an equivalence-like verdict string exists in sbgv7")
if not re.search(r"does not (prove|imply)|not (a )?proof|never (reports|claims) equivalence|not equivalence", readme, re.I):
    fail("capabilities", "README lacks the NO_DIVERGENCE_OBSERVED != equivalence statement")
for feat in ("S3", "explorer", "module E", "internal_divergence"):
    m = re.search(rf"\*\*Not implemented\*\*:[^\n]*{re.escape(feat)}", readme)
    if not m: fail("capabilities", f"README does not list '{feat}' under Not implemented")
for f in ("sbgv7/explorer.py", "sbgv7/s3.py", "sbgv7/state.py"):
    if (ROOT / f).exists(): fail("capabilities", f"{f} exists but README says it is not implemented")
if not (ROOT / "LICENSE").exists() and "LICENSE" in readme: fail("capabilities", "README cites LICENSE which is missing")

# 5 unsupported-claim blacklist (case-insensitive) outside negations is approximated by simple phrases
for d, t in texts.items():
    for pat in (r"state[- ]of[- ]the[- ]art", r"\boutperforms?\b", r"proves? (program )?equivalence", r"independent (hold-?out|benchmark) (result|evaluation) (shows|confirm)",
                r"generali[sz]es (well )?(across|to)", r"verified on linux", r"\bpeer[- ]reviewed\b(?! )(?!.*not)"):
        for m in re.finditer(pat, t, re.I):
            line = t[:m.start()].count("\n") + 1
            ctx = t.splitlines()[line - 1].lower()
            if any(n in ctx for n in ("not ", "no ", "never", "without", "must not", "unsupported", "do not", "does not")): continue
            fail("claims", f"{d}:{line}: possible unsupported claim: {m.group(0)!r}")

print("\n".join(fails) if fails else "V7-B documentation checks: ALL PASSED")
sys.exit(1 if fails else 0)
