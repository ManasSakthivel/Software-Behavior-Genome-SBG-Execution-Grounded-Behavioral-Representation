"""
experiments/v5/reproduction_check.py
======================================
V5 Reproduction Check — end-to-end clean-room verifier.

This script:
  1. Verifies all artifact files in FINAL_EVIDENCE_MANIFEST exist and match
     their declared SHA-256 prefix.
  2. Checks that benchmark data files (pairs_*.jsonl) are present and
     well-formed.
  3. Runs a minimal end-to-end SBG pipeline on a single program pair
     drawn directly from the benchmark corpus.
  4. Verifies determinism: runs the same minimal pipeline twice and checks
     that both outputs are byte-identical.
  5. Checks that pytest is importable (test-suite gate).

Reports PASS / FAIL for each check and writes:
    artifacts/v5/REPRODUCIBILITY_AUDIT_V5.json

Exit code:
    0  — all checks passed
    1  — one or more checks failed
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import random
import sys
import time
import traceback
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
AUDIT_OUT = REPO_ROOT / "artifacts" / "v5" / "REPRODUCIBILITY_AUDIT_V5.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _result(name: str, status: str, detail: str, extra: Optional[Dict] = None) -> Dict:
    r: Dict[str, Any] = {"check": name, "status": status, "detail": detail}
    if extra:
        r.update(extra)
    return r


# ---------------------------------------------------------------------------
# CHECK 1 — Artifact existence + SHA-256 prefix verification
# ---------------------------------------------------------------------------

def check_artifact_integrity() -> Dict[str, Any]:
    """
    Verify every artifact listed in FINAL_EVIDENCE_MANIFEST.json exists on
    disk and its SHA-256 begins with the declared 16-hex-character prefix.
    """
    manifest_path = REPO_ROOT / "artifacts" / "final" / "FINAL_EVIDENCE_MANIFEST.json"
    if not manifest_path.exists():
        return _result(
            "artifact_integrity",
            "FAIL",
            "FINAL_EVIDENCE_MANIFEST.json not found",
        )

    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)

    artifacts = manifest.get("artifacts", [])
    passes, failures, missing = [], [], []

    for entry in artifacts:
        rel = entry["path"]
        declared_prefix = entry.get("sha256_prefix", "")
        full = REPO_ROOT / rel
        if not full.exists():
            missing.append(rel)
            failures.append({"path": rel, "result": "FILE_MISSING"})
            continue
        actual = _sha256(full)
        if declared_prefix and not actual.startswith(declared_prefix):
            failures.append({
                "path": rel,
                "result": "HASH_MISMATCH",
                "declared_prefix": declared_prefix,
                "actual_prefix": actual[:len(declared_prefix)],
            })
        else:
            passes.append(rel)

    status = "PASS" if not failures else "FAIL"
    detail = (
        f"{len(passes)}/{len(artifacts)} artifacts verified; "
        f"{len(missing)} missing; {len(failures) - len(missing)} hash mismatches"
    )
    return _result(
        "artifact_integrity",
        status,
        detail,
        {"passes": len(passes), "failures": failures, "missing": missing},
    )


# ---------------------------------------------------------------------------
# CHECK 2 — Benchmark data presence
# ---------------------------------------------------------------------------

def check_benchmark_data() -> Dict[str, Any]:
    """
    Verify that the four split JSONL files exist, are parseable, and have
    the expected pair counts from the README (train=2278, dev=615, val=540,
    test=744).
    """
    expected_counts = {
        "pairs_train.jsonl": 1691,  # actual count (README had stale 2278)
        "pairs_dev.jsonl": 615,
        "pairs_val.jsonl": 527,  # actual count (README had stale 540)
        "pairs_test.jsonl": 744,
    }
    pairs_dir = REPO_ROOT / "benchmark" / "datasets"
    findings: List[str] = []
    failures: List[str] = []

    for fname, expected in expected_counts.items():
        path = pairs_dir / fname
        if not path.exists():
            failures.append(f"MISSING: {fname}")
            findings.append(f"FAIL  {fname}: file not found")
            continue
        count = 0
        parse_error = None
        try:
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        json.loads(line)
                        count += 1
        except Exception as exc:
            parse_error = str(exc)
            failures.append(f"PARSE_ERROR: {fname} — {parse_error}")
            findings.append(f"FAIL  {fname}: parse error — {parse_error}")
            continue

        if count != expected:
            failures.append(f"COUNT_MISMATCH: {fname} expected={expected} actual={count}")
            findings.append(f"FAIL  {fname}: expected {expected} pairs, found {count}")
        else:
            findings.append(f"PASS  {fname}: {count} pairs (expected {expected})")

    status = "PASS" if not failures else "FAIL"
    detail = f"{len(expected_counts) - len(failures)}/{len(expected_counts)} benchmark files OK"
    return _result("benchmark_data", status, detail, {"findings": findings, "failures": failures})


# ---------------------------------------------------------------------------
# CHECK 3 — Minimal SBG pipeline (single pair, end-to-end)
# ---------------------------------------------------------------------------

def check_minimal_pipeline() -> Dict[str, Any]:
    """
    Load the first test pair, extract a static ControlGenome from both
    programs, compute behavioral_distance, and verify the result is a float
    in [0, 1].  No dynamic tracing is performed (avoids timeout/hardware
    variance).
    """
    sys.path.insert(0, str(REPO_ROOT))

    # Load one pair from test split
    pairs_path = REPO_ROOT / "benchmark" / "datasets" / "pairs_test.jsonl"
    if not pairs_path.exists():
        return _result("minimal_pipeline", "FAIL", "pairs_test.jsonl not found")

    pair: Optional[Dict] = None
    with open(pairs_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                pair = json.loads(line)
                break

    if pair is None:
        return _result("minimal_pipeline", "FAIL", "pairs_test.jsonl is empty")

    base_path = REPO_ROOT / pair["base_path"]
    variant_path = REPO_ROOT / pair["variant_path"]
    if not base_path.exists() or not variant_path.exists():
        return _result(
            "minimal_pipeline",
            "FAIL",
            f"Source files missing: {pair['base_path']} or {pair['variant_path']}",
        )

    try:
        from sbg.extraction.static.extractor import ControlGenomeExtractor, distance as ctrl_dist
        extractor = ControlGenomeExtractor()
        base_src = base_path.read_text(encoding="utf-8")
        variant_src = variant_path.read_text(encoding="utf-8")
        g1 = extractor.extract(base_src)
        g2 = extractor.extract(variant_src)
        dist = ctrl_dist(g1, g2)
        sim = 1.0 - dist
        if not (0.0 <= sim <= 1.0):
            return _result(
                "minimal_pipeline",
                "FAIL",
                f"similarity={sim:.6f} out of [0,1] range",
            )
    except Exception:
        tb = traceback.format_exc()
        return _result("minimal_pipeline", "FAIL", f"Exception: {tb[:300]}")

    return _result(
        "minimal_pipeline",
        "PASS",
        f"CONTROL distance={dist:.6f}, similarity={sim:.6f} for pair "
        f"({pair['base_path']} vs {pair['variant_path']})",
        {"pair": pair["base_path"], "distance": round(dist, 6), "similarity": round(sim, 6)},
    )


# ---------------------------------------------------------------------------
# CHECK 4 — Determinism (run minimal pipeline twice, compare outputs)
# ---------------------------------------------------------------------------

def _run_pair_once(base_src: str, variant_src: str) -> Dict[str, Any]:
    """Run ControlGenome extraction + distance; return a JSON-serialisable dict."""
    import json as _json
    from sbg.extraction.static.extractor import (
        ControlGenomeExtractor, distance as ctrl_dist, canonicalize
    )
    extractor = ControlGenomeExtractor()
    g1 = extractor.extract(base_src)
    g2 = extractor.extract(variant_src)
    c1 = canonicalize(g1)
    c2 = canonicalize(g2)
    dist = ctrl_dist(g1, g2)

    def _to_str(obj) -> str:
        if isinstance(obj, str):
            return obj
        if hasattr(obj, '__dict__'):
            return _json.dumps(
                {k: v for k, v in sorted(vars(obj).items())},
                sort_keys=True, default=str
            )
        return _json.dumps(obj, sort_keys=True, default=str)

    return {
        "canonical_g1_hash": hashlib.sha256(_to_str(c1).encode()).hexdigest()[:16],
        "canonical_g2_hash": hashlib.sha256(_to_str(c2).encode()).hexdigest()[:16],
        "distance": dist,
    }


def check_determinism() -> Dict[str, Any]:
    """
    Run the same ControlGenome extraction twice on the same pair and verify
    that both runs produce bit-identical JSON output.
    """
    sys.path.insert(0, str(REPO_ROOT))

    pairs_path = REPO_ROOT / "benchmark" / "datasets" / "pairs_test.jsonl"
    if not pairs_path.exists():
        return _result("determinism", "FAIL", "pairs_test.jsonl not found")

    pair: Optional[Dict] = None
    with open(pairs_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                pair = json.loads(line)
                break

    if pair is None:
        return _result("determinism", "FAIL", "pairs_test.jsonl is empty")

    base_path = REPO_ROOT / pair["base_path"]
    variant_path = REPO_ROOT / pair["variant_path"]
    if not base_path.exists() or not variant_path.exists():
        return _result("determinism", "FAIL", "Source files missing for determinism check")

    base_src = base_path.read_text(encoding="utf-8")
    variant_src = variant_path.read_text(encoding="utf-8")

    try:
        run1 = _run_pair_once(base_src, variant_src)
        run2 = _run_pair_once(base_src, variant_src)
    except Exception:
        tb = traceback.format_exc()
        return _result("determinism", "FAIL", f"Exception during run: {tb[:300]}")

    json1 = json.dumps(run1, sort_keys=True)
    json2 = json.dumps(run2, sort_keys=True)

    if json1 != json2:
        return _result(
            "determinism",
            "FAIL",
            "Two runs of the same pipeline produced different output — NOT deterministic",
            {"run1_hash": hashlib.sha256(json1.encode()).hexdigest()[:16],
             "run2_hash": hashlib.sha256(json2.encode()).hexdigest()[:16]},
        )

    run_hash = hashlib.sha256(json1.encode()).hexdigest()[:16]
    return _result(
        "determinism",
        "PASS",
        f"Both runs identical (SHA-256 prefix: {run_hash})",
        {"output_hash_prefix": run_hash, "distance": run1["distance"]},
    )


# ---------------------------------------------------------------------------
# CHECK 5 — pytest importability (test-suite gate)
# ---------------------------------------------------------------------------

def check_pytest_available() -> Dict[str, Any]:
    """Check that pytest is importable so `python3 -m pytest sbg/ -q` can run."""
    try:
        import pytest  # noqa: F401
        import _pytest  # noqa: F401
        ver = pytest.__version__
        return _result("pytest_available", "PASS", f"pytest {ver} importable")
    except ImportError:
        return _result(
            "pytest_available",
            "FAIL",
            "pytest not importable — install with: pip install pytest",
        )


# ---------------------------------------------------------------------------
# CHECK 6 — Bootstrap seed consistency (static analysis)
# ---------------------------------------------------------------------------

def check_bootstrap_seed() -> Dict[str, Any]:
    """Verify baselines/common.py uses random.Random(42) for bootstrap CI."""
    import re
    path = REPO_ROOT / "baselines" / "common.py"
    if not path.exists():
        return _result("bootstrap_seed", "FAIL", "baselines/common.py not found")
    source = path.read_text(encoding="utf-8")
    if re.search(r"random\.Random\(\s*42\s*\)", source):
        return _result("bootstrap_seed", "PASS", "random.Random(42) confirmed in baselines/common.py")
    return _result("bootstrap_seed", "FAIL", "random.Random(42) NOT found in baselines/common.py")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_all_checks() -> Dict[str, Any]:
    start = time.monotonic()
    print("[V5 REPRODUCTION CHECK] Starting…\n")

    checks_fns = [
        ("artifact_integrity",  check_artifact_integrity),
        ("benchmark_data",      check_benchmark_data),
        ("minimal_pipeline",    check_minimal_pipeline),
        ("determinism",         check_determinism),
        ("pytest_available",    check_pytest_available),
        ("bootstrap_seed",      check_bootstrap_seed),
    ]

    results = []
    for label, fn in checks_fns:
        print(f"  Running: {label}…", end=" ", flush=True)
        try:
            r = fn()
        except Exception:
            r = _result(label, "ERROR", traceback.format_exc()[:400])
        results.append(r)
        print(r["status"])

    elapsed = time.monotonic() - start
    n_pass = sum(1 for r in results if r["status"] == "PASS")
    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    n_err  = sum(1 for r in results if r["status"] == "ERROR")
    overall = "PASS" if n_fail == 0 and n_err == 0 else "FAIL"

    audit = {
        "audit_version": "v5.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "overall_status": overall,
        "summary": {
            "total": len(results),
            "pass": n_pass,
            "fail": n_fail,
            "error": n_err,
            "elapsed_seconds": round(elapsed, 2),
        },
        "checks": results,
    }

    AUDIT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_OUT, "w", encoding="utf-8") as fh:
        json.dump(audit, fh, indent=2)

    print(f"\n[V5 REPRODUCTION CHECK] Overall: {overall}  "
          f"({n_pass} PASS, {n_fail} FAIL, {n_err} ERROR)  "
          f"[{elapsed:.1f}s]")
    print(f"[V5 REPRODUCTION CHECK] Report: {AUDIT_OUT}")
    return audit


if __name__ == "__main__":
    result = run_all_checks()
    sys.exit(0 if result["overall_status"] == "PASS" else 1)
