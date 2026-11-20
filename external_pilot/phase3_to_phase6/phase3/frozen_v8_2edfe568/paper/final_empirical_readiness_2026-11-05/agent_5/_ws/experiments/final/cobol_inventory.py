#!/usr/bin/env python3
"""FINAL SPRINT, Part 5: COBOL corpus feasibility audit.  READ-ONLY over the corpus (never writes under COBOLSRC).

  PYTHONHASHSEED=0 python experiments/final/cobol_inventory.py [--root /Users/manassakthivel/Desktop/COBOLSRC]
  -> artifacts/paper_evidence/COBOL_CORPUS_INVENTORY.json

Records, for every file: sha256, size, line count, format, program-id, procedure-division construct census, external-dependency
markers, and GnuCOBOL (cobc 3.2.0) outcomes in a scratch directory under /tmp:
  (a) cobc -fsyntax-only -free/-fixed on the file as-is
  (b) the same after a MECHANICAL, behaviour-free stub (EXEC SQL ... END-EXEC -> CONTINUE) -- used ONLY to establish whether any
      non-SQL logic exists; the stub is not a behavioural oracle and is never used for labels.
No program is executed.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
OUT = REPO / "artifacts" / "paper_evidence" / "COBOL_CORPUS_INVENTORY.json"
PROC_VERBS = ["DISPLAY", "ACCEPT", "MOVE", "COMPUTE", "ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "IF", "EVALUATE", "PERFORM", "CALL", "GO TO",
              "READ", "WRITE", "OPEN", "CLOSE", "STRING", "UNSTRING", "INSPECT"]
SQL_RE = re.compile(r"EXEC\s+SQL.*?END-EXEC", re.I | re.S)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def cobc(args, cwd):
    p = subprocess.run(["cobc", *args], cwd=cwd, capture_output=True, text=True, timeout=30)
    first = next((l for l in (p.stdout + p.stderr).splitlines() if "error" in l), "")
    return {"rc": p.returncode, "first_error": first[-200:]}


def make_stub(text: str) -> str:
    """Mechanical, behaviour-free stub used ONLY for a syntax-feasibility probe of the non-SQL COBOL.
    Data Division: EXEC SQL blocks removed and the host fields a precompiler would supply (SQLCODE, SQLN, SQLD) declared.
    Procedure Division: each EXEC SQL ... END-EXEC becomes CONTINUE.  The stub performs no database access and defines no behaviour."""
    text = re.sub(r"^\s*CBL\b.*$", "", text, flags=re.M | re.I)
    m = re.search(r"procedure\s+division", text, re.I)
    ls = text.rfind("\n", 0, m.start()) + 1 if m else 0          # keep the line's own indentation (Area A/B columns matter)
    head, tail = (text[:ls], text[ls:]) if m else (text, "")
    head = SQL_RE.sub(" ", head)
    head = head.rstrip() + "\n       01  SQLCODE PIC S9(9) COMP-5.\n       01  SQLN PIC S9(4) COMP-5.\n       01  SQLD PIC S9(4) COMP-5.\n\n"
    tail = SQL_RE.sub("CONTINUE", tail)
    return head + tail


def census(text: str):
    """Procedure-division verbs outside EXEC SQL blocks (comment lines removed)."""
    t = SQL_RE.sub(" ", text)
    lines = [l for l in t.splitlines() if not (len(l) > 6 and l[6] == "*") and not l.lstrip().startswith("*>")]
    body = "\n".join(lines)
    m = re.search(r"procedure\s+division", body, re.I)
    proc = body[m.end():] if m else ""
    return {v: len(re.findall(r"\b" + v.replace(" ", r"\s+") + r"\b", proc, re.I)) for v in PROC_VERBS}, bool(m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/Users/manassakthivel/Desktop/COBOLSRC")
    a = ap.parse_args()
    root = pathlib.Path(a.root)
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.name != ".DS_Store")
    ver = subprocess.run(["cobc", "--version"], capture_output=True, text=True).stdout.splitlines()[0]
    scratch = pathlib.Path(tempfile.mkdtemp(prefix="cobinv_"))
    rows, by_hash = [], collections.defaultdict(list)
    for p in files:
        raw = p.read_bytes()
        text = raw.decode("utf-8", "replace")
        rel = str(p.relative_to(root))
        h = sha(raw)
        by_hash[h].append(rel)
        row = {"path": rel, "sha256": h, "bytes": len(raw), "lines": text.count("\n") + (0 if text.endswith("\n") else 1), "ext": p.suffix}
        if p.suffix == ".cbl":
            n_sql = len(SQL_RE.findall(text))
            verbs, has_proc = census(text)
            row.update(kind="program", program_id=(re.search(r'program-id\.\s*"?([\w-]+)"?', text, re.I) or [None, None])[1],
                       has_procedure_division=has_proc, n_exec_sql_blocks=n_sql, has_cbl_compiler_directive=bool(re.match(r"\s*CBL\b", text, re.I)),
                       sql_include_sqlca=bool(re.search(r"INCLUDE\s+SQLCA", text, re.I)), n_copy_statements=len(re.findall(r"\bCOPY\s+[\w-]+", text, re.I)),
                       non_sql_procedure_verbs={k: v for k, v in verbs.items() if v}, has_file_io=bool(re.search(r"\bSELECT\s+[\w-]+\s+ASSIGN", text, re.I)),
                       has_stop_run=bool(re.search(r"stop\s+run", text, re.I)))
            d = pathlib.Path(tempfile.mkdtemp(dir=scratch))
            src = d / "p.cbl"
            src.write_bytes(raw)
            row["cobc_as_is"] = {"free": cobc(["-fsyntax-only", "-free", "p.cbl"], d), "fixed": cobc(["-fsyntax-only", "-fixed", "p.cbl"], d)}
            stub = make_stub(text)
            (d / "s.cbl").write_text(stub)
            row["cobc_after_mechanical_sql_stub"] = {"fixed": cobc(["-fsyntax-only", "-fixed", "s.cbl"], d)}
        else:
            row.update(kind="copybook" if p.suffix == ".cpy" else "other", n_exec_sql_blocks=len(SQL_RE.findall(text)),
                       defines_data=bool(re.search(r"^\s*\d\d\s+[\w-]+", text, re.M)))
        rows.append(row)
    progs = [r for r in rows if r["kind"] == "program"]
    uniq_progs = {r["sha256"] for r in progs}
    summary = {
        "root": str(root), "cobc": ver, "n_files": len(rows), "n_cbl": len(progs), "n_unique_cbl_sha256": len(uniq_progs),
        "n_cpy": sum(1 for r in rows if r["kind"] == "copybook"),
        "files_per_directory": dict(collections.Counter(str(pathlib.Path(r["path"]).parent) for r in rows)),
        "duplicate_groups": [v for v in by_hash.values() if len(v) > 1],
        "n_cbl_with_procedure_division": sum(1 for r in progs if r["has_procedure_division"]),
        "n_cbl_with_exec_sql": sum(1 for r in progs if r["n_exec_sql_blocks"]),
        "n_cbl_with_any_non_sql_procedure_verb": sum(1 for r in progs if r["non_sql_procedure_verbs"]),
        "non_sql_verbs_total": dict(sum((collections.Counter(r["non_sql_procedure_verbs"]) for r in progs), collections.Counter())),
        "n_cbl_with_file_io": sum(1 for r in progs if r["has_file_io"]),
        "n_cbl_with_copy_stmt": sum(1 for r in progs if r["n_copy_statements"]),
        "n_cbl_with_cbl_directive": sum(1 for r in progs if r["has_cbl_compiler_directive"]),
        "cobc_as_is_syntax_ok_free": sum(1 for r in progs if r["cobc_as_is"]["free"]["rc"] == 0),
        "cobc_as_is_syntax_ok_fixed": sum(1 for r in progs if r["cobc_as_is"]["fixed"]["rc"] == 0),
        "cobc_after_stub_syntax_ok_fixed": sum(1 for r in progs if r["cobc_after_mechanical_sql_stub"]["fixed"]["rc"] == 0),
        "total_lines_cbl": sum(r["lines"] for r in progs), "max_lines_cbl": max(r["lines"] for r in progs), "min_lines_cbl": min(r["lines"] for r in progs),
        "n_test_or_fixture_files": sum(1 for r in rows if re.search(r"test|expected|\.in$|\.out$|\.dat$", r["path"], re.I)),
        "license_or_provenance_files_found": [r["path"] for r in rows if re.search(r"licen|readme|copying|notice", r["path"], re.I)],
        "first_error_histogram_as_is_fixed": dict(collections.Counter(re.sub(r"^.*?error: ", "", r["cobc_as_is"]["fixed"]["first_error"])[:90] for r in progs).most_common(6)),
    }
    OUT.write_text(json.dumps({"artifact": "COBOL_CORPUS_INVENTORY", "summary": summary, "files": rows}, indent=1) + "\n")
    shutil.rmtree(scratch, ignore_errors=True)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
