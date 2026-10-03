#!/usr/bin/env python3
"""
experiments/final/consistency_check.py
======================================
Scientific-integrity gate. Fails the build when the repository disagrees with
its own evidence.

Checks
------
C1  generated tables    re-runs make_tables.py into a temporary directory and
                        diffs. A committed table can never drift from the
                        artifact it was generated from.
C2  manifest agreement  every pair count in the manifest adds up, and the six
                        split intersections are empty.
C3  denominators        no result artifact reports a sample size larger than
                        the number of pairs it actually scored.
C4  provenance          no document cites an artifact that is not MEASURED.
C5  retired claims      strings that the evidence has withdrawn must not appear
                        in any current document. Each is listed with the reason
                        and the correct replacement.
C6  oracle attribution  no current document attributes an output-reading result
                        to SBG.
C7  output-free         the output-free protocol traces no self-test driver.

Archived documents under docs/archive/ are exempt from C5 and C6: they are the
historical record, and rewriting them would destroy the evidence of what was
claimed when.

Usage:
    python3 experiments/final/consistency_check.py [--verbose]
Exit code 0 when every check passes, 1 otherwise.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile
from typing import List, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
GENERATED_DIR = REPO_ROOT / "docs" / "generated"
ARCHIVE_DIR = REPO_ROOT / "docs" / "archive"

# Strings the evidence has withdrawn. Each entry: (pattern, why, replacement).
RETIRED_CLAIMS: List[Tuple[str, str, str]] = [
    (r"3,?777\s+(?:program\s+)?pairs",
     "the benchmark has 3577 pairs on disk, not 3777",
     "3,577 nominal pairs (benchmark/benchmark_manifest.json)"),
    (r"99\s+Python\s+programs",
     "the corpus holds 64 program files, 60 of which are assigned to splits",
     "60 programs assigned to splits (64 files on disk)"),
    (r"516\s+(?:unit\s+)?tests",
     "the suite contains 545 tests",
     "the count printed by `make test`"),
    (r"\b12/12\b",
     "the 12/12 hard-negative score belongs to the output-reading reference, "
     "not to SBG; SBG V5 scores 5/12 at tau*=0.08",
     "output-reading reference 12/12; SBG V5 5/12"),
    (r"\b14/15\b",
     "the 14/15 regression score belongs to the output-reading reference, not "
     "to SBG",
     "output-reading reference 13/15; SBG V5 7/15"),
    (r"9/9\*{0,2}\s+detected",
     "no silent-bug result of 9/9 is supported; SBG V5 detects 3/9",
     "SBG V5 3/9 on silent bugs"),
    (r"Behavioral oracle",
     "this label was applied to an output comparison",
     "output-reading reference"),
    (r"744\s+test\s+pairs\)",
     "744 is the nominal split size; the published AUROC was computed over 643",
     "state the nominal and the evaluated denominator separately"),
]

# Phrases that would attribute an output-reading result to SBG.
ORACLE_MISATTRIBUTION = [
    (r"SBG[^.\n]{0,40}\boutput\s+oracle\b", "names SBG and the output oracle together"),
]

# Every Markdown file at the repository root is current by definition: a stale
# "final status" document left at the root is exactly what a reader finds first.
DOC_GLOBS = ("*.md", "CITATION.cff", "docs/*.md", "docs/current/*.md")

# A retired claim may be quoted while it is being withdrawn -- that is how a
# correction is written. A match is allowed when its line, or the table header
# a few lines above it, carries one of these markers. Quoting a withdrawn number
# without one of them is what the check is for.
WITHDRAWAL_MARKERS = (
    "previously reported", "previously", "withdrawn", "retired", "superseded",
    "output-reading", "output reading", "not an sbg result", "reads output",
    "corrected", "was reported", "were reported", "reported under",
    "attributed", "no longer", "instead of", "actually", "claimed",
)
CONTEXT_LINES = 4


def current_documents() -> List[pathlib.Path]:
    paths: List[pathlib.Path] = []
    for pattern in DOC_GLOBS:
        paths.extend(sorted(REPO_ROOT.glob(pattern)))
    return [p for p in paths
            if ARCHIVE_DIR not in p.parents and GENERATED_DIR not in p.parents]


def check_generated_tables() -> Tuple[bool, List[str]]:
    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "experiments" / "final" / "make_tables.py"),
             "--out-dir", tmp],
            capture_output=True, text=True, cwd=REPO_ROOT)
        if result.returncode != 0:
            return False, [f"make_tables.py failed: {result.stderr.strip()}"]
        problems = []
        for regenerated in sorted(pathlib.Path(tmp).iterdir()):
            committed = GENERATED_DIR / regenerated.name
            if not committed.exists():
                problems.append(f"{regenerated.name}: not committed under docs/generated/")
            elif committed.read_text() != regenerated.read_text():
                problems.append(f"{regenerated.name}: committed copy differs from the "
                                "artifact it is generated from; run `make tables`")
        return not problems, problems


def check_manifest() -> Tuple[bool, List[str]]:
    path = REPO_ROOT / "benchmark" / "benchmark_manifest.json"
    if not path.exists():
        return False, ["benchmark/benchmark_manifest.json missing; run `make manifest`"]
    manifest = json.loads(path.read_text())
    problems = []
    for name, block in manifest["datasets"].items():
        if not block["all_intersections_empty"]:
            for key, shared in block["split_program_intersections"].items():
                if shared:
                    problems.append(f"{name}: splits {key} share programs {shared}")
        totals = block["totals"]
        summed = sum(s["nominal_pairs"] for s in block["splits"].values())
        if summed != totals["nominal_pairs"]:
            problems.append(f"{name}: split pair counts sum to {summed} but totals "
                            f"say {totals['nominal_pairs']}")
        for split, s in block["splits"].items():
            if s["changed_pairs"] + s["equivalent_pairs"] != s["nominal_pairs"]:
                problems.append(f"{name}/{split}: CHANGED + EQUIVALENT != nominal")
    corpus = manifest["corpus"]
    if (corpus["n_assigned_to_splits"] + corpus["n_unassigned"]
            != corpus["n_files_on_disk"]):
        problems.append("corpus: assigned + unassigned != files on disk")
    return not problems, problems


def check_denominators() -> Tuple[bool, List[str]]:
    problems = []
    for path in sorted((REPO_ROOT / "artifacts" / "final").glob("MAIN_EVALUATION_*.json")):
        name = path.name
        payload = json.loads(path.read_text())
        sizes = payload["set_sizes"]
        if not sizes["VALID"] <= sizes["EVALUABLE"] <= sizes["ALL"]:
            problems.append(f"{name}: set sizes are not nested "
                            f"VALID <= EVALUABLE <= ALL: {sizes}")
        ledger_total = sum(payload["failure_ledger"].values())
        if sizes["ALL"] - sizes["EVALUABLE"] != ledger_total:
            problems.append(f"{name}: {sizes['ALL'] - sizes['EVALUABLE']} pairs are "
                            f"unevaluated but the failure ledger accounts for "
                            f"{ledger_total}")
        for set_name, block in payload["results"].items():
            for predictor, stats in block["predictors"].items():
                if stats.get("auroc") is None:
                    continue
                if stats["n"] != sizes[set_name]:
                    problems.append(f"{name}/{set_name}/{predictor}: n={stats['n']} "
                                    f"but the set holds {sizes[set_name]}")
    return not problems, problems


def check_provenance() -> Tuple[bool, List[str]]:
    path = REPO_ROOT / "artifacts" / "final" / "ARTIFACT_PROVENANCE.json"
    if not path.exists():
        return False, ["artifacts/final/ARTIFACT_PROVENANCE.json missing"]
    registry = json.loads(path.read_text())["artifacts"]
    not_measured = {relative for relative, record in registry.items()
                    if record["status"] != "MEASURED"}
    problems = []
    for document in current_documents():
        text = document.read_text()
        for relative in not_measured:
            basename = pathlib.Path(relative).name
            for match in re.finditer(re.escape(basename), text):
                line_start = text.rfind("\n", 0, match.start()) + 1
                line = text[line_start:text.find("\n", match.start())]
                # Citing a non-measured artifact is only allowed while saying so.
                status = registry[relative]["status"]
                lines = text.splitlines()
                line_index = text.count("\n", 0, match.start())
                context = " ".join(
                    lines[max(0, line_index - CONTEXT_LINES):line_index + 1]).lower()
                if not (status.lower() in context
                        or any(token in context for token in
                               ("superseded", "not reproduce", "does not reproduce",
                                "synthetic", "provenance", "withdrawn", "corrected",
                                "records", "claims"))):
                    problems.append(
                        f"{document.relative_to(REPO_ROOT)}: cites {basename} "
                        f"(status {status}) without saying so")
    return not problems, problems


def _is_withdrawn_in_context(lines: List[str], line_index: int) -> bool:
    window = lines[max(0, line_index - CONTEXT_LINES):line_index + 1]
    haystack = " ".join(window).lower()
    return any(marker in haystack for marker in WITHDRAWAL_MARKERS)


def check_retired_claims() -> Tuple[bool, List[str]]:
    problems = []
    for document in current_documents():
        text = document.read_text()
        lines = text.splitlines()
        for pattern, reason, replacement in RETIRED_CLAIMS:
            for match in re.finditer(pattern, text):
                line_index = text.count("\n", 0, match.start())
                if _is_withdrawn_in_context(lines, line_index):
                    continue
                problems.append(
                    f"{document.relative_to(REPO_ROOT)}:{line_index + 1}: retired "
                    f"claim {match.group(0)!r} -- {reason}. Use: {replacement}")
    return not problems, problems


def check_oracle_attribution() -> Tuple[bool, List[str]]:
    problems = []
    for document in current_documents():
        text = document.read_text()
        for pattern, reason in ORACLE_MISATTRIBUTION:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                line_no = text.count("\n", 0, match.start()) + 1
                line_start = text.rfind("\n", 0, match.start()) + 1
                line = text[line_start:text.find("\n", match.start())]
                if any(token in line.lower() for token in
                       ("not an sbg", "reference", "ceiling", "not sbg",
                        "reads output", "previously")):
                    continue
                problems.append(f"{document.relative_to(REPO_ROOT)}:{line_no}: "
                                f"{reason}: {match.group(0)!r}")
    return not problems, problems


def check_readme_block() -> Tuple[bool, List[str]]:
    """The README's results section must equal the generated block verbatim."""
    readme = REPO_ROOT / "README.md"
    generated = GENERATED_DIR / "readme_results.md"
    if not generated.exists():
        return False, ["docs/generated/readme_results.md missing; run `make tables`"]
    text = readme.read_text()
    begin, end = "<!-- BEGIN GENERATED RESULTS -->", "<!-- END GENERATED RESULTS -->"
    start, stop = text.find(begin), text.find(end)
    if start == -1 or stop == -1:
        return False, [f"README.md is missing {begin} / {end}"]
    embedded = text[start:stop + len(end)].strip()
    if embedded != generated.read_text().strip():
        return False, ["README.md's generated results block differs from "
                       "docs/generated/readme_results.md; run `make readme`"]
    return True, []


def check_output_free_protocol() -> Tuple[bool, List[str]]:
    paths = sorted((REPO_ROOT / "artifacts" / "final").glob("programs_*output_free*.json"))
    if not paths:
        return True, ["skipped: output-free protocol has not been run"]
    problems = []
    records = {}
    for path in paths:
        records.update(json.loads(path.read_text())["programs"])
    for program_path, record in records.items():
        discovery = record.get("entry_discovery") or ""
        entry = discovery.split(":")[-1]
        if entry.startswith("test_") or entry in ("main", "demo"):
            problems.append(f"{program_path}: output-free protocol selected the "
                            f"scaffolding entry point {entry!r}")
    return not problems, problems


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hash_claims(node, found):
    """Every {path-like: ..., sha256: ...} pair anywhere inside a freeze record."""
    if isinstance(node, dict):
        digest = node.get("sha256")
        target = next((node[k] for k in ("path", "file", "relative_path")
                       if isinstance(node.get(k), str)), None)
        if isinstance(digest, str) and target:
            found.append((target, digest))
        for key, value in node.items():
            if key.endswith("_sha256") and isinstance(value, str) and len(value) == 64:
                stem = key[:-len("_sha256")]
                if isinstance(node.get(stem), str):
                    found.append((node[stem], value))
            _hash_claims(value, found)
    elif isinstance(node, list):
        for value in node:
            _hash_claims(value, found)
    return found


def check_frozen_inputs() -> Tuple[bool, List[str]]:
    """Nothing that was frozen before scoring may have changed since.

    Covers the pre-registration, the benchmark pair files (test-set
    modification), the threshold (it must come from dev), and every hash a
    stage recorded in an artifacts/final/freeze_*.json record (corpus manifests,
    generated negatives, weights).
    """
    problems = []
    final = REPO_ROOT / "artifacts" / "final"
    freeze = final / "PHASE2_FREEZE.json"
    if freeze.exists():
        record = json.loads(freeze.read_text())
        doc = REPO_ROOT / record["preregistration"]
        if not doc.exists() or _sha256(doc) != record["preregistration_sha256"]:
            problems.append(f"{record['preregistration']} changed after it was frozen")
    manifest = json.loads((REPO_ROOT / "benchmark" / "benchmark_manifest.json").read_text())
    for name, block in manifest["datasets"].items():
        for split, s in block["splits"].items():
            pairs = REPO_ROOT / s["pairs_file"]
            if not pairs.exists() or _sha256(pairs) != s["pairs_file_sha256"]:
                problems.append(f"{name}/{split}: {s['pairs_file']} differs from the "
                                "manifest -- the benchmark changed without a new version")
    threshold = final / "THRESHOLD_FROZEN.json"
    if threshold.exists():
        t = json.loads(threshold.read_text())
        text = json.dumps(t).lower()
        if t.get("split", "dev") != "dev" or "pairs_test" in text:
            problems.append("THRESHOLD_FROZEN.json: threshold must be derived from dev only")
    for record_path in sorted(final.glob("freeze_*.json")):
        for target, digest in _hash_claims(json.loads(record_path.read_text()), []):
            path = pathlib.Path(target)
            path = path if path.is_absolute() else REPO_ROOT / path
            if path.is_file() and _sha256(path) != digest:
                problems.append(f"{record_path.name}: {target} changed after it was frozen")
            elif not path.exists():
                problems.append(f"{record_path.name}: frozen file {target} is missing")
    return not problems, problems


def check_gate() -> Tuple[bool, List[str]]:
    """The gate verdict is recomputed from artifacts, and documents quote it exactly."""
    gate_script = REPO_ROOT / "experiments" / "final" / "stanford_gate.py"
    gate_artifact = REPO_ROOT / "artifacts" / "final" / "STANFORD_GATE.json"
    if not gate_script.exists() or not gate_artifact.exists():
        return False, ["the evidence-driven gate has not been run; run `make gate`"]
    result = subprocess.run([sys.executable, str(gate_script), "--check"],
                            capture_output=True, text=True, cwd=REPO_ROOT)
    problems = []
    if result.returncode not in (0, 1):
        problems.append(f"stanford_gate.py --check crashed: {result.stderr.strip()[-300:]}")
    recomputed = json.loads(result.stdout) if result.stdout.strip().startswith("{") else None
    committed = json.loads(gate_artifact.read_text())
    if recomputed is None or recomputed.get("categories") != committed.get("categories"):
        problems.append("STANFORD_GATE.json differs from the verdict recomputed from "
                        "the artifacts on disk; run `make gate`")
    n_pass = committed.get("summary", {}).get("pass")
    n_total = committed.get("summary", {}).get("total")
    for document in current_documents():
        text = document.read_text()
        for match in re.finditer(r"\b(\d{1,2})/(\d{1,2})\s+PASS\b", text):
            quoted = (int(match.group(1)), int(match.group(2)))
            if quoted[1] == n_total and quoted != (n_pass, n_total):
                line_no = text.count("\n", 0, match.start()) + 1
                problems.append(f"{document.relative_to(REPO_ROOT)}:{line_no}: quotes "
                                f"{match.group(0)!r} but the gate artifact says "
                                f"{n_pass}/{n_total} PASS")
    return not problems, problems


CHECKS = [
    ("C1 generated tables match their artifacts", check_generated_tables),
    ("C2 benchmark manifest is internally consistent", check_manifest),
    ("C3 result denominators agree with the sets", check_denominators),
    ("C4 documents cite only MEASURED artifacts", check_provenance),
    ("C5 no retired claim appears in a current document", check_retired_claims),
    ("C6 no output-reading result is attributed to SBG", check_oracle_attribution),
    ("C7 output-free protocol traces no self-test driver", check_output_free_protocol),
    ("C8 README results block matches the generated tables", check_readme_block),
    ("C9 frozen inputs are unchanged (prereg, benchmark, threshold, corpora)",
     check_frozen_inputs),
    ("C10 gate verdict is recomputed from artifacts and quoted exactly", check_gate),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    failures = 0
    for label, check in CHECKS:
        passed, messages = check()
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {label}")
        if not passed:
            failures += 1
        if messages and (args.verbose or not passed):
            for message in messages[:40]:
                print(f"         {message}")
            if len(messages) > 40:
                print(f"         ... and {len(messages) - 40} more")
    print(f"\n{len(CHECKS) - failures}/{len(CHECKS)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
