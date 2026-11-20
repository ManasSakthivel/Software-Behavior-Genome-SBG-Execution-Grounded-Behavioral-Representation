#!/usr/bin/env python3
"""
experiments/final/external_quixbugs.py
======================================
QuixBugs (Python) external evaluation under the corrected output-free
protocol. Implements docs/current/PHASE2_PREREGISTRATION.md §6.

Stages
------
  prepare   Write external/quixbugs/manifest.json, which applies the static
            eligibility rules to every file. Generate the SP negatives under
            external/quixbugs/variants/. Hash both into
            artifacts/final/freeze_quixbugs.json. Nothing is executed here.
  score     Execute every pair of the frozen manifest under ``--protocol`` in
            both input regimes, and write the per-pair JSONL. Each program runs
            in its own subprocess, so a non-terminating buggy program cannot
            slow the programs traced after it by leaving threads behind. That
            is harness isolation only; the measurement is unchanged.
  analyse   Compute statistics from the per-pair JSONL: AUROC, cluster
            bootstrap, permutation, Holm, and the metrics at the frozen τ*.

Input regimes
-------------
  canonical  (primary)   The protocol's own entry selection and synthesised
                         inputs. It is the frozen protocol, applied unchanged.
  declared   (secondary) The QuixBugs function named after the file, called on
                         the input half of ``json_testcases``. Expected outputs
                         are discarded by ``load_declared_inputs`` and never
                         reach this module's other code.

Declared-regime entry mapping
-----------------------------
Fixed before scoring, and structural only. Transformation SP-2 renames
functions, so an SP variant may no longer define a function with the program's
name. In that case the entry is the top-level function at the same ordinal
position among top-level ``def``s as in the fixed program. The rule is
recorded in each row as ``entry_mapping``.

Usage::

    python3 experiments/final/external_quixbugs.py prepare
    python3 experiments/final/external_quixbugs.py score   --protocol output_free_v7
    python3 experiments/final/external_quixbugs.py analyse --protocol output_free_v7
"""
from __future__ import annotations

import argparse
import ast
import concurrent.futures
import datetime
import itertools
import json
import os
import pathlib
import re
import subprocess
import sys
import threading
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.final import external_common as ec                 # noqa: E402

CORPUS = "quixbugs"
QB_DIR = REPO_ROOT / "external" / "quixbugs"
BUGGY_DIR = QB_DIR / "python_programs"
FIXED_DIR = QB_DIR / "correct_python_programs"
TESTCASE_DIR = QB_DIR / "json_testcases"
VARIANT_DIR = QB_DIR / "variants"
MANIFEST_PATH = QB_DIR / "manifest.json"
FREEZE_PATH = ec.ARTIFACT_DIR / "freeze_quixbugs.json"

UPSTREAM = "https://github.com/jkoppel/QuixBugs"
UPSTREAM_COMMIT = "4257f44b0ff1181dedaedee6a447e133219fcebf"
LICENSE = "MIT"
REGIMES = ("canonical", "declared")
PRIMARY_REGIME = "canonical"
WORKER_TIMEOUT_S = 900
PARALLEL_WORKERS = 3
REFERENCE_CALL_TIMEOUT_S = 1.0
REFERENCE_MAX_ITEMS = 10000


# ---------------------------------------------------------------------------
# Declared inputs — the ONLY reader of json_testcases
# ---------------------------------------------------------------------------

def load_declared_inputs(path: pathlib.Path) -> List[tuple]:
    """Input half of each QuixBugs test case; the expected output is dropped here.

    Each line is ``[args, expected]``. Only ``args`` survives this function.
    """
    inputs: List[tuple] = []
    for line in pathlib.Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        case = json.loads(line)
        args = case[0]
        del case                       # the expected output goes no further
        inputs.append(tuple(args) if isinstance(args, list) else (args,))
    return inputs


# ---------------------------------------------------------------------------
# Static interface helpers
# ---------------------------------------------------------------------------

def top_level_functions(source: str) -> List[str]:
    tree = ast.parse(source)
    return [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def function_signature(source: str, name: str) -> Optional[dict]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            args = node.args
            positional = [a.arg for a in list(args.posonlyargs) + list(args.args)]
            return {"params": positional, "n_required": len(positional) - len(args.defaults),
                    "is_generator": any(isinstance(n, (ast.Yield, ast.YieldFrom))
                                        for n in ast.walk(node))}
    return None


def resolve_declared_entry(program_id: str, fixed_source: str,
                           source: str) -> Tuple[Optional[str], str]:
    """Entry for the declared regime (see module docstring)."""
    names = top_level_functions(source)
    if program_id in names:
        return program_id, "by_name"
    fixed_names = top_level_functions(fixed_source)
    if program_id in fixed_names:
        index = fixed_names.index(program_id)
        if index < len(names):
            return names[index], f"by_ordinal:{index}"
    return None, "unresolved"


def _is_scaffolding(filename: str) -> Optional[str]:
    if filename.endswith("_test.py"):
        return "scaffolding: QuixBugs test driver (constructs graphs, prints results)"
    if filename == "node.py":
        return "scaffolding: shared Node helper class, not a subject program"
    return None


# ---------------------------------------------------------------------------
# prepare
# ---------------------------------------------------------------------------

def prepare() -> int:
    from experiments.final.protocol import eligible_candidates

    if VARIANT_DIR.exists():
        for stale in VARIANT_DIR.glob("*.py"):
            stale.unlink()
    files = sorted(p.name for p in BUGGY_DIR.glob("*.py"))
    programs: List[dict] = []
    scaffolding: List[dict] = []
    for filename in files:
        reason = _is_scaffolding(filename)
        if reason:
            scaffolding.append({"file": f"python_programs/{filename}", "status": "excluded",
                                "reason": reason})
            continue
        program_id = filename[:-3]
        buggy_path, fixed_path = BUGGY_DIR / filename, FIXED_DIR / filename
        entry: Dict[str, Any] = {
            "id": program_id,
            "source_repository": UPSTREAM,
            "commit": UPSTREAM_COMMIT,
            "license": LICENSE,
            "language": "python",
            "buggy_path": ec.rel(buggy_path),
            "fixed_path": ec.rel(fixed_path),
            "split": "external_test",
            "written_for_sbg": False,
        }
        if not fixed_path.exists():
            entry.update({"eligible": {"canonical": False, "declared": False},
                          "exclusion_reason": "no fixed version upstream"})
            programs.append(entry)
            continue
        buggy_src, fixed_src = buggy_path.read_text(), fixed_path.read_text()
        entry["interface"] = {
            "top_level_functions": top_level_functions(fixed_src),
            "named_entry": function_signature(fixed_src, program_id),
            "annotated": False,
        }
        # canonical: the protocol's static eligibility rule, on both versions
        canon_ok = bool(eligible_candidates(ast.parse(fixed_src))) and \
            bool(eligible_candidates(ast.parse(buggy_src)))
        testcase = TESTCASE_DIR / f"{program_id}.json"
        declared_reason = None
        if not testcase.exists():
            declared_reason = "no json_testcases upstream (graph program exercised only by a *_test.py driver)"
        elif function_signature(fixed_src, program_id) is None or \
                function_signature(buggy_src, program_id) is None:
            declared_reason = "no top-level function named after the program"
        entry["declared_inputs"] = {
            "file": ec.rel(testcase) if testcase.exists() else None,
            "n_cases": len(load_declared_inputs(testcase)) if testcase.exists() else 0,
        }
        entry["eligible"] = {"canonical": canon_ok, "declared": declared_reason is None}
        entry["exclusion_reason"] = {
            "canonical": None if canon_ok else "no function synthesisable under the protocol",
            "declared": declared_reason,
        }
        accepted, rejected = ec.generate_sp_negatives(fixed_path, VARIANT_DIR, program_id)
        entry["negatives"] = accepted
        entry["negatives_rejected"] = rejected
        programs.append(entry)

    manifest = {
        "corpus": CORPUS,
        "source_repository": UPSTREAM,
        "commit": UPSTREAM_COMMIT,
        "license": LICENSE,
        "frozen_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "preregistration": "docs/current/PHASE2_PREREGISTRATION.md",
        "eligibility_rules": {
            "subject": "every python_programs/*.py except *_test.py drivers and node.py",
            "canonical": "protocol.eligible_candidates non-empty on both fixed and buggy "
                         "versions (static; identical rule to the main benchmark)",
            "declared": "json_testcases file exists and both versions define a top-level "
                        "function named after the program",
        },
        "negatives_rule": {"order": list(ec.SP_ORDER), "seed": ec.SP_SEED,
                           "max_per_program": ec.N_NEGATIVES,
                           "accept_if": "compiles and normalised AST differs from fixed"},
        "declared_entry_mapping": "by name; if an SP-2 variant renamed it, the top-level "
                                  "function at the same ordinal position as in the fixed program",
        "counts": {
            "files": len(files),
            "scaffolding_excluded": len(scaffolding),
            "subject_programs": len(programs),
            "eligible_canonical": sum(1 for p in programs if p["eligible"]["canonical"]),
            "eligible_declared": sum(1 for p in programs if p["eligible"]["declared"]),
            "negatives": sum(len(p.get("negatives", [])) for p in programs),
        },
        "programs": programs,
        "scaffolding": scaffolding,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")

    variant_files = sorted(VARIANT_DIR.glob("*.py"))
    corpus_files = sorted(itertools.chain(BUGGY_DIR.glob("*.py"), FIXED_DIR.glob("*.py"),
                                          TESTCASE_DIR.glob("*.json")))
    freeze = {
        "artifact": "FREEZE_QUIXBUGS",
        "frozen_at": manifest["frozen_at"],
        "note": "Written by `prepare`, before any QuixBugs pair was executed or scored.",
        "preregistration_sha256": ec.sha256_file(REPO_ROOT / "docs/current/PHASE2_PREREGISTRATION.md"),
        "manifest": {"path": ec.rel(MANIFEST_PATH), "sha256": ec.sha256_file(MANIFEST_PATH)},
        "negatives": ec.hash_files(variant_files),
        "corpus": {k: v for k, v in ec.hash_files(corpus_files).items() if k != "files"},
        "upstream": {"repository": UPSTREAM, "commit": UPSTREAM_COMMIT},
    }
    ec.write_freeze(FREEZE_PATH, freeze)
    print(json.dumps(manifest["counts"], indent=2))
    print(f"wrote {ec.rel(MANIFEST_PATH)}, {ec.rel(FREEZE_PATH)}")
    return 0


def verify_freeze() -> dict:
    """Refuse to score if the manifest or negatives changed since the freeze."""
    freeze = json.loads(FREEZE_PATH.read_text())
    if ec.sha256_file(MANIFEST_PATH) != freeze["manifest"]["sha256"]:
        raise SystemExit("manifest changed since freeze; refusing to score")
    now = ec.hash_files(sorted(VARIANT_DIR.glob("*.py")))
    if now["combined_sha256"] != freeze["negatives"]["combined_sha256"]:
        raise SystemExit("negatives changed since freeze; refusing to score")
    return {"path": ec.rel(FREEZE_PATH), "sha256": ec.sha256_file(FREEZE_PATH),
            "manifest_sha256": freeze["manifest"]["sha256"],
            "negatives_sha256": freeze["negatives"]["combined_sha256"]}


# ---------------------------------------------------------------------------
# Output-reading reference (LABELLED; never an SBG result)
# ---------------------------------------------------------------------------

_ADDR = re.compile(r" at 0x[0-9a-fA-F]+")


def _call_observed(fn, args: tuple) -> str:
    box: Dict[str, str] = {}

    def run() -> None:
        import copy
        try:
            value = fn(*copy.deepcopy(args))
            if hasattr(value, "__next__") and hasattr(value, "__iter__"):
                value = list(itertools.islice(value, REFERENCE_MAX_ITEMS))
            box["out"] = "value:" + _ADDR.sub(" at 0x?", repr(value))
        except BaseException as exc:                               # noqa: BLE001
            box["out"] = "raise:" + type(exc).__name__

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(REFERENCE_CALL_TIMEOUT_S)
    return box.get("out", "timeout")


def output_reference(base_path: str, base_entry: str, variant_path: str,
                     variant_entry: str, inputs: List[tuple]) -> dict:
    import importlib.util
    import io

    def load(path: str, tag: str):
        spec = importlib.util.spec_from_file_location(f"_qb_ref_{tag}", path)
        module = importlib.util.module_from_spec(spec)
        saved = sys.stdout
        sys.stdout = io.StringIO()
        try:
            spec.loader.exec_module(module)                        # type: ignore[union-attr]
        finally:
            sys.stdout = saved
        return module

    try:
        fb = getattr(load(base_path, "b"), base_entry)
        fv = getattr(load(variant_path, "v"), variant_entry)
    except BaseException as exc:                                   # noqa: BLE001
        return {"differs": None, "error": f"{type(exc).__name__}: {exc}"}
    saved = sys.stdout
    sys.stdout = io.StringIO()
    try:
        observed = [(_call_observed(fb, a), _call_observed(fv, a)) for a in inputs]
    finally:
        sys.stdout = saved
    mismatches = sum(1 for a, b in observed if a != b)
    return {"differs": mismatches > 0, "n_inputs": len(inputs), "n_mismatches": mismatches}


# ---------------------------------------------------------------------------
# Worker: one program, one regime, in its own process
# ---------------------------------------------------------------------------

def _pairs_for(entry: dict) -> List[Tuple[str, int, str, str, str]]:
    """(pair_id, label, kind, base_path, variant_path) — base is always the fixed program."""
    pid = entry["id"]
    pairs = [(f"{CORPUS}__{pid}__bug", 1, "real_bug", entry["fixed_path"], entry["buggy_path"])]
    for neg in entry.get("negatives", []):
        pairs.append((f"{CORPUS}__{pid}__{neg['transformation_type'].lower()}_s{neg['seed']}",
                      0, f"sp_negative:{neg['transformation_type']}",
                      entry["fixed_path"], neg["path"]))
    return pairs


def worker(program_id: str, regime: str, protocol: str) -> List[dict]:
    from experiments.final import extraction as ex

    manifest = json.loads(MANIFEST_PATH.read_text())
    entry = next(p for p in manifest["programs"] if p["id"] == program_id)
    budgets = protocol if protocol in ex.TRACE_TIMEOUT_S else "output_free_v6"
    cache: Dict[str, Any] = {}
    fixed_abs = str(REPO_ROOT / entry["fixed_path"])
    fixed_src = (REPO_ROOT / entry["fixed_path"]).read_text()
    inputs = (load_declared_inputs(REPO_ROOT / entry["declared_inputs"]["file"])
              if regime == "declared" else None)

    def record(path_rel: str):
        path_abs = str(REPO_ROOT / path_rel)
        if regime == "canonical":
            return ex.extract_program(path_abs, cache, protocol), None
        name, how = resolve_declared_entry(program_id, fixed_src, (REPO_ROOT / path_rel).read_text())
        if name is None:
            return ex.ProgramRecord(path=path_abs, ok=False, failure_kind="no_entry_function",
                                    failure_detail="declared entry unresolved"), how
        return ex.extract_with_inputs(path_abs, cache, name, inputs, budgets_from=budgets), how

    rows: List[dict] = []
    base_rec, base_map = record(entry["fixed_path"])
    # Trace order: fixed, then the SP negatives, then the buggy program last.
    # A non-terminating buggy program leaves timed-out tracer threads spinning in
    # this process; tracing it last keeps them from contending with (and
    # spuriously timing out) any other trace. Output-reference calls, which can
    # also time out, run only after every trace has been taken.
    pairs = sorted(_pairs_for(entry), key=lambda pair: pair[1] == 1)
    traced = [(pair, record(pair[4])) for pair in pairs]
    for (pair_id, label, kind, base_rel, variant_rel), (variant_rec, variant_map) in traced:
        scores = ex.score_pair(base_rec, variant_rec)
        static = ec.static_scores((REPO_ROOT / base_rel).read_text(),
                                  (REPO_ROOT / variant_rel).read_text())
        extra: Dict[str, Any] = {"regime": regime}
        if regime == "declared":
            extra["entry_mapping"] = {"base": base_map, "variant": variant_map}
            b_name, _ = resolve_declared_entry(program_id, fixed_src, fixed_src)
            v_name, _ = resolve_declared_entry(program_id, fixed_src,
                                               (REPO_ROOT / variant_rel).read_text())
            extra["output_reference"] = (
                output_reference(fixed_abs, b_name, str(REPO_ROOT / variant_rel), v_name, inputs)
                if b_name and v_name else {"differs": None, "error": "entry unresolved"})
        rows.append(ec.make_row(
            pair_id=f"{pair_id}__{regime}", corpus=CORPUS, base_id=program_id, label=label,
            kind=kind, regime=regime, protocol=protocol, base_path=base_rel,
            variant_path=variant_rel, base_summary=_summary(base_rec),
            variant_summary=_summary(variant_rec), scores=scores, static=static, extra=extra))
    return rows


def _summary(record) -> dict:
    summary = record.summary()
    summary["path"] = ec.rel(pathlib.Path(summary["path"]))
    return summary


def _run_worker(args: Tuple[str, str, str]) -> Tuple[str, str, List[dict], Optional[str]]:
    program_id, regime, protocol = args
    cmd = [sys.executable, str(pathlib.Path(__file__).resolve()), "worker",
           "--program", program_id, "--regime", regime, "--protocol", protocol]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT),
                              timeout=WORKER_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return program_id, regime, [], f"harness_timeout: worker exceeded {WORKER_TIMEOUT_S}s"
    marker = "@@ROWS@@"
    if proc.returncode != 0 or marker not in proc.stdout:
        return program_id, regime, [], f"worker_failed (rc={proc.returncode}): {proc.stderr.strip()[-400:]}"
    payload = proc.stdout.split(marker, 1)[1]
    return program_id, regime, json.loads(payload), None


def _failed_rows(entry: dict, regime: str, protocol: str, kind: str, detail: str) -> List[dict]:
    rows = []
    for pair_id, label, pkind, base_rel, variant_rel in _pairs_for(entry):
        static = ec.static_scores((REPO_ROOT / base_rel).read_text(),
                                  (REPO_ROOT / variant_rel).read_text())
        rows.append(ec.make_row(
            pair_id=f"{pair_id}__{regime}", corpus=CORPUS, base_id=entry["id"], label=label,
            kind=pkind, regime=regime, protocol=protocol, base_path=base_rel,
            variant_path=variant_rel,
            base_summary={"ok": False, "failure_kind": kind, "failure_detail": detail},
            variant_summary=None, scores=None, static=static,
            extra={"regime": regime}))
    return rows


def pairs_path(regime: str, protocol: str) -> pathlib.Path:
    return ec.ARTIFACT_DIR / f"pairs_quixbugs_{regime}_{protocol}.jsonl"


def score(protocol: str) -> int:
    from experiments.final import extraction as ex
    if protocol not in ex.PROTOCOLS:
        raise SystemExit(f"protocol {protocol!r} not in extraction.PROTOCOLS {ex.PROTOCOLS}")
    freeze = verify_freeze()
    manifest = json.loads(MANIFEST_PATH.read_text())
    jobs, rows_by_regime = [], {r: [] for r in REGIMES}
    for entry in manifest["programs"]:
        for regime in REGIMES:
            if entry["eligible"][regime]:
                jobs.append((entry["id"], regime, protocol))
            else:
                rows_by_regime[regime].extend(_failed_rows(
                    entry, regime, protocol, "ineligible",
                    entry["exclusion_reason"][regime] or "ineligible"))
    by_id = {p["id"]: p for p in manifest["programs"]}
    with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
        for program_id, regime, rows, error in pool.map(_run_worker, jobs):
            if error:
                rows = _failed_rows(by_id[program_id], regime, protocol, "harness_error", error)
            rows_by_regime[regime].extend(rows)
            n_ok = sum(1 for r in rows if r["evaluated"])
            print(f"  [{protocol}/{regime}] {program_id:28s} {n_ok}/{len(rows)} evaluated"
                  + (f"  ({error[:80]})" if error else ""), flush=True)
    for regime in REGIMES:
        rows = sorted(rows_by_regime[regime], key=lambda r: r["pair_id"])
        for row in rows:
            row["freeze_sha256"] = freeze["sha256"]
        pairs_path(regime, protocol).write_text(
            "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
        print(f"wrote {ec.rel(pairs_path(regime, protocol))} ({len(rows)} pairs)")
    return 0


# ---------------------------------------------------------------------------
# analyse
# ---------------------------------------------------------------------------

def analyse(protocol: str) -> int:
    from experiments.final.extraction import PREDICTORS
    freeze = verify_freeze()
    manifest = json.loads(MANIFEST_PATH.read_text())
    tau, tau_meta = ec.read_frozen_threshold()
    if tau is not None and tau_meta and tau_meta.get("protocol") not in (None, protocol):
        tau_note = (f"τ* was frozen under {tau_meta.get('protocol')}, scoring under {protocol}; "
                    "τ*-dependent metrics are reported but are cross-protocol")
    else:
        tau_note = None
    predictors = [p for p in PREDICTORS]
    regimes: Dict[str, Any] = {}
    for regime in REGIMES:
        rows = [json.loads(l) for l in pairs_path(regime, protocol).read_text().splitlines() if l.strip()]
        programs = {r["base_id"] for r in rows}
        evaluated_programs = {r["base_id"] for r in rows if r["evaluated"]}
        pos_eval_programs = {r["base_id"] for r in rows if r["evaluated"] and r["label"] == 1}
        regimes[regime] = {
            "role": "primary" if regime == PRIMARY_REGIME else "secondary",
            "program_counts": {
                "subject_programs": len(programs),
                "eligible": sum(1 for p in manifest["programs"] if p["eligible"][regime]),
                "with_any_evaluated_pair": len(evaluated_programs),
                "with_evaluated_real_bug_pair": len(pos_eval_programs),
                "excluded_by_rule": sorted(
                    {p["id"]: p["exclusion_reason"][regime] for p in manifest["programs"]
                     if not p["eligible"][regime]}.items()),
            },
            "pair_counts": {
                "total": len(rows),
                "positive": sum(1 for r in rows if r["label"] == 1),
                "negative": sum(1 for r in rows if r["label"] == 0),
                "evaluated": sum(1 for r in rows if r["evaluated"]),
                "evaluated_positive": sum(1 for r in rows if r["evaluated"] and r["label"] == 1),
                "evaluated_negative": sum(1 for r in rows if r["evaluated"] and r["label"] == 0),
            },
            "failed_pairs": [
                {"pair_id": r["pair_id"], "side": r["failure_side"], "kind": r["failure_kind"],
                 "detail": (r["failure_detail"] or "")[:160]}
                for r in rows if not r["evaluated"]],
            "statistics": ec.analyse_rows(rows, predictors, tau),
        }
    result = {
        "experiment": "QUIXBUGS_EXTERNAL_EVALUATION",
        "corpus": CORPUS,
        "protocol": protocol,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "preregistration": "docs/current/PHASE2_PREREGISTRATION.md §6",
        "upstream": {"repository": UPSTREAM, "commit": UPSTREAM_COMMIT, "license": LICENSE},
        "freeze": freeze,
        "manifest_counts": manifest["counts"],
        "tau_star": {"value": tau, "source": tau_meta, "note": tau_note}
        if tau is not None else {"value": None, "note": "THRESHOLD_FROZEN.json absent: "
                                 "τ*-dependent metrics not computed"},
        "primary": {"regime": PRIMARY_REGIME, "set": "EVALUABLE", "predictor": ec.PRIMARY,
                    "holm_family": list(ec.COMPARATORS)},
        "labels": {"1": "real QuixBugs bug (fixed vs buggy)",
                   "0": "semantics-preserving variant of the fixed program"},
        "unit_of_independence": "program (cluster bootstrap / within-cluster permutation by program)",
        "statistics_config": {"n_bootstrap": ec.N_BOOTSTRAP, "n_permutations": ec.N_PERMUTATIONS,
                              "n_shuffles": ec.N_SHUFFLES, "seed": ec.SEED},
        "output_free_note": "SBG and every execution predictor read traces only. The "
                            "output_reference field compares return values and is an "
                            "output-reading ceiling, never an SBG result.",
        "regimes": regimes,
        "per_pair_artifacts": {r: ec.rel(pairs_path(r, protocol)) for r in REGIMES},
    }
    out = ec.ARTIFACT_DIR / f"QUIXBUGS_{protocol}.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {ec.rel(out)}")
    for regime in REGIMES:
        block = regimes[regime]["statistics"]["sets"]["EVALUABLE"]["predictors"]
        v5 = block.get("sbg_v5", {})
        print(f"  {regime:9s} EVALUABLE sbg_v5 AUROC={v5.get('auroc')} CI={v5.get('ci95_cluster_bootstrap')} "
              f"n={v5.get('n')} programs={v5.get('n_clusters')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=("prepare", "score", "analyse", "worker"))
    parser.add_argument("--protocol", default="output_free_v7")
    parser.add_argument("--program")
    parser.add_argument("--regime", choices=REGIMES)
    args = parser.parse_args()
    if args.stage == "prepare":
        return prepare()
    if args.stage == "score":
        return score(args.protocol)
    if args.stage == "analyse":
        return analyse(args.protocol)
    rows = worker(args.program, args.regime, args.protocol)
    sys.stdout.write("@@ROWS@@" + json.dumps(rows))
    sys.stdout.flush()
    os._exit(0)                        # abandon any timed-out tracer threads


if __name__ == "__main__":
    raise SystemExit(main())
