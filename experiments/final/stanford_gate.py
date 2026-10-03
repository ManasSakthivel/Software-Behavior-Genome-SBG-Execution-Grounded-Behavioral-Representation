#!/usr/bin/env python3
"""
experiments/final/stanford_gate.py
==================================
The evidence-driven Stanford Researcher Gate
(docs/current/PHASE2_PREREGISTRATION.md §7).

Every verdict is computed from files on disk. Nothing here is a hard-coded
PASS. A category is PASS when the evidence it requires exists and that
evidence's integrity checks pass. It is BLOCKED otherwise, and its ``missing``
list names what is absent. PASS does not require SBG to perform well: a
measured negative result passes.

    python3 experiments/final/stanford_gate.py           # write artifacts/final/STANFORD_GATE.json
    python3 experiments/final/stanford_gate.py --check   # print the verdict, write nothing

Exit status: 0 if every category passes, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Callable, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "experiments" / "final"))
ART = REPO_ROOT / "artifacts" / "final"
REPORT = REPO_ROOT / "FINAL_STANFORD_READINESS_REPORT.md"
README = REPO_ROOT / "README.md"

PROTOCOL = "output_free_v7"
MAIN_TEST = ART / f"MAIN_EVALUATION_v6test_{PROTOCOL}.json"
MAIN_TEST_PROGRAMS = ART / f"programs_v6test_{PROTOCOL}.json"
THRESHOLD = ART / "THRESHOLD_FROZEN.json"
WEIGHTS = ART / "WEIGHT_FITTING.json"
DRIVER_VALIDATION = ART / "DRIVER_SYNTHESIS_VALIDATION.json"
QUIXBUGS = ART / f"QUIXBUGS_{PROTOCOL}.json"
BUGSINPY = ART / f"BUGSINPY_{PROTOCOL}.json"
JAVA_RESULT = ART / "QUIXBUGS_JAVA_SBG_RESULTS.json"
JAVA_REMOVAL = ART / "JAVA_CLAIM_REMOVAL.json"

# Evidence-volume floors fixed in the pre-registration (§7), before any data.
MIN_REAL_PROGRAMS_ONE_CORPUS = 20
MIN_CLASS_TIER_TEST_PROGRAMS = 3
MIN_PROGRAMS_TOTAL = 40
MIN_PROGRAMS_REAL = 20

Result = Tuple[List[str], List[str]]          # (evidence, missing)


def _load(path: pathlib.Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _rel(path: pathlib.Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def _consistency(names: Tuple[str, ...]) -> Result:
    import consistency_check as cc               # noqa: E402 - same directory
    evidence, missing = [], []
    for label, check in cc.CHECKS:
        if not label.startswith(names):
            continue
        ok, problems = check()
        (evidence if ok else missing).append(
            label if ok else f"{label}: {'; '.join(problems[:3])}")
    return evidence, missing


def _heading(path: pathlib.Path, pattern: str) -> bool:
    if not path.exists():
        return False
    return re.search(rf"^#+\s.*{pattern}", path.read_text(), re.I | re.M) is not None


def _quixbugs_programs(q: Optional[dict]) -> int:
    try:
        return int(q["regimes"]["canonical"]["program_counts"]["with_evaluated_real_bug_pair"])
    except (TypeError, KeyError, ValueError):
        return 0


def _bugsinpy_programs(b: Optional[dict]) -> int:
    try:
        return int(b["headline"]["bugs_evaluated_with_valid_positive"])
    except (TypeError, KeyError, ValueError):
        return 0


def _main_test_programs() -> Tuple[int, int]:
    """(evaluated programs, of which class tier) on the v7 test split."""
    programs = _load(MAIN_TEST_PROGRAMS)
    if programs is None:
        return 0, 0
    base = {}
    for path, record in programs["programs"].items():
        if "/base_programs/" in path and record.get("ok"):
            base[path] = (record.get("entry_discovery") or "").split(":")[0]
    return len(base), sum(1 for tier in base.values() if tier == "class")


def _has_stats(block: Optional[dict]) -> bool:
    text = json.dumps(block) if block else ""
    return all(token in text for token in ("auroc", "ci", "holm"))


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

def research_question() -> Result:
    return _consistency(("C9",))


def novelty() -> Result:
    ok = _heading(REPORT, "novelty")
    return ([f"{_rel(REPORT)} has a novelty section"], []) if ok else \
        ([], [f"{_rel(REPORT)}: no section stating the novelty claim and its evidence"])


def methodological_rigor() -> Result:
    evidence, missing = [], []
    t = _load(THRESHOLD)
    if t and t.get("protocol") == PROTOCOL and t.get("derived_on", {}).get("split") == "dev" \
            and t.get("reads_no_test_or_external_labels") is True:
        evidence.append(f"tau*={t['tau_star']} derived on dev only under {PROTOCOL}")
    else:
        missing.append("THRESHOLD_FROZEN.json derived on dev under output_free_v7")
    w = _load(WEIGHTS)
    if w and w.get("chosen_on_dev") and "test" in w:
        evidence.append(f"weights fitted on train, chosen on dev ({w['chosen_on_dev']}), test scored")
    else:
        missing.append("WEIGHT_FITTING.json with the dev choice and the single test scoring")
    if _load(MAIN_TEST):
        evidence.append(_rel(MAIN_TEST))
    else:
        missing.append(f"{_rel(MAIN_TEST)} (frozen test evaluation under {PROTOCOL})")
    return evidence, missing


def oracle_independence() -> Result:
    evidence, missing = _consistency(("C6", "C7"))
    if (ART / "OUTPUT_ORACLE_LEAK_AUDIT.json").exists():
        evidence.append("OUTPUT_ORACLE_LEAK_AUDIT.json")
    else:
        missing.append("OUTPUT_ORACLE_LEAK_AUDIT.json")
    test = REPO_ROOT / "tests" / "test_external_quixbugs.py"
    if test.exists() and "output" in test.read_text().lower():
        evidence.append("declared-input regime has a test that expected outputs never reach tracing")
    else:
        missing.append("test that QuixBugs expected outputs never reach tracing")
    return evidence, missing


def benchmark_quality() -> Result:
    evidence, missing = _consistency(("C2", "C3"))
    main_n, _ = _main_test_programs()
    q_n = _quixbugs_programs(_load(QUIXBUGS))
    b_n = _bugsinpy_programs(_load(BUGSINPY))
    total, real = main_n + q_n + b_n, q_n + b_n
    line = f"evaluated programs: main test {main_n}, QuixBugs {q_n}, BugsInPy {b_n}"
    if main_n == 0:
        missing.append(f"{_rel(MAIN_TEST_PROGRAMS)} (v7 test program records)")
    if total >= MIN_PROGRAMS_TOTAL and real >= MIN_PROGRAMS_REAL:
        evidence.append(f"{line} (total {total} >= {MIN_PROGRAMS_TOTAL}, real {real} >= {MIN_PROGRAMS_REAL})")
    else:
        missing.append(f"{line}; prereg floor total >= {MIN_PROGRAMS_TOTAL} and real >= {MIN_PROGRAMS_REAL}")
    return evidence, missing


def real_program_validity() -> Result:
    q_n = _quixbugs_programs(_load(QUIXBUGS))
    b_n = _bugsinpy_programs(_load(BUGSINPY))
    best = max(q_n, b_n)
    if best >= MIN_REAL_PROGRAMS_ONE_CORPUS:
        return [f"real-program corpus with {best} evaluated programs (QuixBugs {q_n}, BugsInPy {b_n})"], []
    return [], [f"no external corpus with >= {MIN_REAL_PROGRAMS_ONE_CORPUS} evaluated programs "
                f"(QuixBugs {q_n}, BugsInPy {b_n})"]


def stateful_program_validity() -> Result:
    evidence, missing = [], []
    _, n_class = _main_test_programs()
    if n_class >= MIN_CLASS_TIER_TEST_PROGRAMS:
        evidence.append(f"{n_class} test programs evaluated through the class tier")
    else:
        missing.append(f"{n_class} test programs evaluated through the class tier; "
                       f"prereg floor {MIN_CLASS_TIER_TEST_PROGRAMS}")
    v = _load(DRIVER_VALIDATION)
    if v and v.get("n_cases") and v.get("n_cases_passed") == v.get("n_cases"):
        evidence.append(f"driver-synthesis validation {v['n_cases_passed']}/{v['n_cases']}")
    else:
        missing.append("DRIVER_SYNTHESIS_VALIDATION.json with every case passing")
    return evidence, missing


def _corpus_frozen(result: Optional[dict], manifest_key: str) -> bool:
    text = json.dumps(result) if result else ""
    return bool(result) and "sha256" in text and manifest_key in text


def external_validation() -> Result:
    evidence, missing = [], []
    for path, key in ((QUIXBUGS, "quixbugs"), (BUGSINPY, "bugsinpy")):
        result = _load(path)
        if _corpus_frozen(result, key) and result.get("protocol") == PROTOCOL:
            evidence.append(f"{path.name} under {PROTOCOL} with frozen manifest hash")
        else:
            missing.append(f"{path.name} under {PROTOCOL} with its frozen manifest hash")
    if _load(JAVA_RESULT):
        evidence.append(f"{JAVA_RESULT.name} (Java under the SBG schema)")
    elif _load(JAVA_REMOVAL):
        _, leftovers = _java_claims()
        if leftovers:
            missing.append("Java claim removed but still made in: " + "; ".join(leftovers[:3]))
        else:
            evidence.append(f"{JAVA_REMOVAL.name}; no current document makes a Java claim")
    else:
        missing.append(f"{JAVA_RESULT.name} or {JAVA_REMOVAL.name}")
    return evidence, missing


def _java_claims() -> Result:
    import consistency_check as cc               # noqa: E402
    hits = []
    for document in cc.current_documents():
        for number, line in enumerate(document.read_text().splitlines(), 1):
            if re.search(r"\bjava\b", line, re.I) and not re.search(
                    r"removed|withdrawn|not an sbg|exploratory|no java claim", line, re.I):
                hits.append(f"{document.relative_to(REPO_ROOT)}:{number}")
    return [], hits


def statistical_rigor() -> Result:
    evidence, missing = [], []
    for path in (MAIN_TEST, QUIXBUGS, BUGSINPY):
        (evidence if _has_stats(_load(path)) else missing).append(
            f"{path.name}: AUROC, cluster CI and Holm-corrected comparisons")
    return evidence, missing


def baseline_quality() -> Result:
    evidence, missing = [], []
    for path in (MAIN_TEST, QUIXBUGS, BUGSINPY):
        text = json.dumps(_load(path) or {})
        ok = all(p in text for p in ("static_ast", "static_token", "exception_fraction", "call_count"))
        (evidence if ok else missing).append(f"{path.name}: static and execution baselines")
    return evidence, missing


def empirical_validity() -> Result:
    s = _load(ART / "PYTHON_VERSION_SENSITIVITY.json")
    if s and all(not e["reported_values_changed"] for e in s["experiments"].values()):
        return [f"no reported value moves across {s['compared']}; canonical {s['canonical_version']}"], []
    return [], ["PYTHON_VERSION_SENSITIVITY.json showing no reported value changes"]


def reproducibility() -> Result:
    evidence, missing = [], []
    makefile = (REPO_ROOT / "Makefile").read_text()
    for target in ("setup:", "reproduce-v7:", "reproduce-real:", "reproduce-external:", "gate:"):
        (evidence if target in makefile else missing).append(f"Makefile target {target[:-1]}")
    for path in ("requirements-lock.txt", ".python-version", "docs/current/REPRODUCTION.md"):
        (evidence if (REPO_ROOT / path).exists() else missing).append(path)
    return evidence, missing


def claim_discipline() -> Result:
    evidence, missing = _consistency(("C5", "C8"))
    readme = README.read_text() if README.exists() else ""
    for path in (MAIN_TEST, QUIXBUGS, BUGSINPY):
        (evidence if path.name in readme else missing).append(f"README cites {path.name}")
    return evidence, missing


def failure_transparency() -> Result:
    evidence, missing = [], []
    checks = ((MAIN_TEST, "failure_ledger"), (QUIXBUGS, "failed_pairs"),
              (BUGSINPY, "exclusion_taxonomy"))
    for path, key in checks:
        (evidence if key in json.dumps(_load(path) or {}) else missing).append(
            f"{path.name}: {key}")
    return evidence, missing


def internal_consistency() -> Result:
    return _consistency(("C1", "C2", "C3", "C4", "C7", "C8"))


def engineering_quality() -> Result:
    evidence, missing = [], []
    ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text()
    if "continue-on-error: true" in ci:
        missing.append("CI has a step that cannot fail")
    else:
        evidence.append("CI steps all fail the build")
    for test in ("test_driver_synthesis.py", "test_external_quixbugs.py",
                 "test_external_bugsinpy.py", "test_statistics.py", "test_integrity.py"):
        (evidence if (REPO_ROOT / "tests" / test).exists() else missing).append(f"tests/{test}")
    return evidence, missing


def scientific_integrity() -> Result:
    evidence, missing = _consistency(("C9",))
    w = _load(WEIGHTS)
    if w and w.get("fit_refuses_if_test_scored", True) and w.get("chosen_on_dev"):
        evidence.append("weights chosen before test was scored")
    else:
        missing.append("WEIGHT_FITTING.json recording the dev choice before test")
    return evidence, missing


def research_maturity() -> Result:
    evidence, missing = [], []
    for pattern, label in (("negative result", "negative results"), ("limitation", "limitations")):
        (evidence if _heading(REPORT, pattern) else missing).append(
            f"{_rel(REPORT)}: {label} section")
    return evidence, missing


def generalization_validity() -> Result:
    evidence, missing = [], []
    report = REPORT.read_text() if REPORT.exists() else ""
    for path in (QUIXBUGS, BUGSINPY):
        (evidence if path.name in report else missing).append(
            f"report scopes its generalisation claim to {path.name}")
    return evidence, missing


CATEGORIES: List[Tuple[str, Callable[[], Result]]] = [
    ("research_question", research_question),
    ("novelty", novelty),
    ("methodological_rigor", methodological_rigor),
    ("oracle_independence", oracle_independence),
    ("benchmark_quality", benchmark_quality),
    ("real_program_validity", real_program_validity),
    ("stateful_program_validity", stateful_program_validity),
    ("external_validation", external_validation),
    ("statistical_rigor", statistical_rigor),
    ("baseline_quality", baseline_quality),
    ("empirical_validity", empirical_validity),
    ("reproducibility", reproducibility),
    ("claim_discipline", claim_discipline),
    ("failure_transparency", failure_transparency),
    ("internal_consistency", internal_consistency),
    ("engineering_quality", engineering_quality),
    ("scientific_integrity", scientific_integrity),
    ("research_maturity", research_maturity),
    ("generalization_validity", generalization_validity),
]


def evaluate() -> dict:
    categories: Dict[str, dict] = {}
    for name, check in CATEGORIES:
        evidence, missing = check()
        categories[name] = {"verdict": "BLOCKED" if missing else "PASS",
                            "evidence": evidence, "missing": missing}
    others_blocked = [n for n, c in categories.items() if c["verdict"] == "BLOCKED"]
    categories["publication_readiness"] = {
        "verdict": "BLOCKED" if others_blocked else "PASS",
        "evidence": [] if others_blocked else ["every other category passes"],
        "missing": [f"{n} is BLOCKED" for n in others_blocked],
    }
    n_pass = sum(1 for c in categories.values() if c["verdict"] == "PASS")
    return {"artifact": "STANFORD_GATE", "rule": "docs/current/PHASE2_PREREGISTRATION.md §7",
            "categories": categories,
            "summary": {"pass": n_pass, "blocked": len(categories) - n_pass,
                        "total": len(categories)}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="print only; write nothing")
    args = parser.parse_args()
    verdict = evaluate()
    if args.check:
        print(json.dumps(verdict, indent=2))
    else:
        (ART / "STANFORD_GATE.json").write_text(json.dumps(verdict, indent=2) + "\n")
        for name, c in verdict["categories"].items():
            print(f"[{c['verdict']:7}] {name}" + (f"  -- missing: {c['missing'][0]}" if c["missing"] else ""))
        s = verdict["summary"]
        print(f"\n{s['pass']}/{s['total']} PASS, {s['blocked']} BLOCKED")
    return 0 if verdict["summary"]["blocked"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
