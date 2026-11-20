"""Structural check of the LaTeX manuscript (not a compile): every \\cite key is in references.bib, every \\ref/\\eqref has a \\label,
every \\input and \\includegraphics target exists, no placeholder markers, and every bib entry carries a doi or url.
Usage (from paper/IEEE_ACCESS_V8_FINAL): python3 scripts/check_manuscript.py   -> exit 0 if clean."""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def strip(s): return re.sub(r"(?<!\\)%.*", "", s)


def tex_files():
    seen, todo = [], ["main.tex"]
    while todo:
        f = todo.pop()
        p = os.path.join(ROOT, f if f.endswith(".tex") else f + ".tex")
        if p in seen: continue
        seen.append(p)
        if os.path.exists(p):
            todo += re.findall(r"\\input\{([^}]+)\}", strip(open(p).read()))
    return seen


def check():
    files = tex_files()
    problems = [f"missing input: {f}" for f in files if not os.path.exists(f)]
    allt = "\n".join(strip(open(f).read()) for f in files if os.path.exists(f))
    entries = [e for e in re.split(r"\n(?=@)", open(os.path.join(ROOT, "references.bib")).read()) if e.strip().startswith("@")]
    keys = {re.match(r"@\w+\{([^,]+),", e.strip()).group(1) for e in entries}
    cites = {k.strip() for g in re.findall(r"\\cite\{([^}]+)\}", allt) for k in g.split(",")}
    problems += [f"undefined cite: {k}" for k in sorted(cites - keys)]
    refs = set(re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", allt))
    problems += [f"undefined ref: {r}" for r in sorted(refs - set(re.findall(r"\\label\{([^}]+)\}", allt)))]
    for g in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", allt):
        if not os.path.exists(os.path.join(ROOT, g)): problems.append(f"missing figure: {g}")
    for pat in (r"\bTODO\b", r"\bTBD\b", r"\?\?", r"XXX"):
        if re.search(pat, allt): problems.append(f"placeholder pattern {pat}")
    problems += [f"bib entry without doi/url: {e.split(',')[0]}" for e in entries if not re.search(r"\b(doi|url)\s*=", e)]
    return problems, len(cites), len(keys), sorted(keys - cites)


if __name__ == "__main__":
    probs, nc, nk, unused = check()
    print(f"cited keys: {nc}; bib entries: {nk}; uncited bib entries: {len(unused)} {unused}")
    print("\n".join(probs) or "OK: no structural problems")
    sys.exit(1 if probs else 0)
