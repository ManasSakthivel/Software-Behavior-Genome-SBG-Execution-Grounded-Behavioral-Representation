"""
experiments/v2/reproducibility_check.py
=========================================
Reproducibility Audit — Agent N.

READ-ONLY audit of the SBG V2 codebase. This script:
  1. Verifies critical artifact files exist.
  2. Checks that result files have the expected keys.
  3. Verifies bootstrap seed=42 in baselines/common.py.
  4. Checks n_runs in b07_dynamic_v2.py — flags SAFEGUARD-6 violation if n_runs=1.
  5. Computes SHA-256 hashes of all critical artifacts.
  6. Writes artifacts/v2/REPRODUCIBILITY_AUDIT.json.

Run:
    python3 experiments/v2/reproducibility_check.py

Exit code:
    0  — audit passed (no violations)
    1  — audit failed (violations found; see REPRODUCIBILITY_AUDIT.json)
"""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import re
import sys
from typing import Any, Dict, List, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
AUDIT_OUT = REPO_ROOT / "artifacts" / "v2" / "REPRODUCIBILITY_AUDIT.json"

# ---------------------------------------------------------------------------
# Critical artifacts that must exist and have known structure
# ---------------------------------------------------------------------------

CRITICAL_ARTIFACTS: List[Dict[str, Any]] = [
    # Phase-gate artifacts (PHASE_0-2 use "gate" key, PHASE_3+ use "phase" key)
    {"path": "artifacts/research/PHASE_0_GATE.json",       "required_keys": ["gate", "status"]},
    {"path": "artifacts/research/PHASE_1_GATE.json",       "required_keys": ["gate", "status"]},
    {"path": "artifacts/research/PHASE_2_GATE.json",       "required_keys": ["gate", "status"]},
    {"path": "artifacts/research/PHASE_3_GATE.json",       "required_keys": ["phase", "status"]},
    {"path": "artifacts/research/PHASE_4_GATE.json",       "required_keys": ["phase", "status"]},
    {"path": "artifacts/research/PHASE_5_GATE.json",       "required_keys": ["phase", "status"]},
    {"path": "artifacts/research/PHASE_6_GATE.json",       "required_keys": ["phase", "status"]},
    # Baseline results
    {"path": "artifacts/phase3/B02/results_test.json",     "required_keys": ["metrics"]},
    {"path": "artifacts/phase3/B08/results_test.json",     "required_keys": ["metrics"]},
    # Phase 4 experiment results
    {"path": "artifacts/phase4/E1/results.json",           "required_keys": []},
    {"path": "artifacts/phase4/E2/results.json",           "required_keys": []},
    {"path": "artifacts/phase4/E3/results.json",           "required_keys": []},
    {"path": "artifacts/phase4/E6/results.json",           "required_keys": []},
    {"path": "artifacts/phase4/E7/results.json",           "required_keys": []},
    {"path": "artifacts/phase4/E10/results.json",          "required_keys": []},
    {"path": "artifacts/phase4/E12/results.json",          "required_keys": []},
    # Phase 5
    {"path": "artifacts/phase5/cross_language_results.json", "required_keys": []},
    {"path": "artifacts/phase5/regression_results.json",    "required_keys": []},
    # Claims registry
    {"path": "docs/CLAIMS_REGISTRY.yaml",                  "required_keys": None},  # YAML, skip key check
    # V2 manifests
    {"path": "artifacts/final/FINAL_REPRODUCIBILITY_MANIFEST.json",
     "required_keys": ["seeds", "reproduction_steps", "artifact_hash_manifest"]},
    {"path": "artifacts/final/FINAL_EVIDENCE_MANIFEST.json",
     "required_keys": ["artifacts"]},
    {"path": "artifacts/v2/PREREGISTRATION_MANIFEST.json",
     "required_keys": ["version", "documents", "attestation"]},
    # Experiment registry
    {"path": "experiments/REGISTRY.yaml", "required_keys": None},
    # Source files being audited
    {"path": "baselines/common.py",                        "required_keys": None},
    {"path": "baselines/v2/b07_dynamic_v2.py",             "required_keys": None},
    {"path": "sbg/v2/execution/runner.py",                 "required_keys": None},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: pathlib.Path) -> Optional[Any]:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        return None


def _check_keys(data: Any, required_keys: List[str]) -> List[str]:
    """Return list of missing keys (top-level only)."""
    if not required_keys:
        return []
    if not isinstance(data, dict):
        return required_keys
    return [k for k in required_keys if k not in data]


# ---------------------------------------------------------------------------
# Check 1: Artifact existence + keys + SHA-256
# ---------------------------------------------------------------------------

def check_artifacts() -> Dict[str, Any]:
    results = []
    violations = []

    for spec in CRITICAL_ARTIFACTS:
        rel = spec["path"]
        full = REPO_ROOT / rel
        exists = full.exists()
        entry: Dict[str, Any] = {
            "path": rel,
            "exists": exists,
            "sha256": None,
            "size_bytes": None,
            "missing_keys": [],
            "parse_error": None,
        }

        if not exists:
            violations.append(f"MISSING_ARTIFACT: {rel}")
        else:
            entry["sha256"] = _sha256(full)
            entry["size_bytes"] = full.stat().st_size

            required_keys = spec.get("required_keys")
            if required_keys is not None and full.suffix == ".json":
                data = _load_json(full)
                if data is None:
                    entry["parse_error"] = "JSON_PARSE_ERROR"
                    violations.append(f"JSON_PARSE_ERROR: {rel}")
                else:
                    missing = _check_keys(data, required_keys)
                    entry["missing_keys"] = missing
                    if missing:
                        violations.append(f"MISSING_KEYS {missing} in {rel}")

        results.append(entry)

    return {"artifact_checks": results, "violations": violations}


# ---------------------------------------------------------------------------
# Check 2: Bootstrap seed in baselines/common.py
# ---------------------------------------------------------------------------

def check_bootstrap_seed() -> Dict[str, Any]:
    """Verify that bootstrap uses seed=42 via random.Random(42)."""
    path = REPO_ROOT / "baselines" / "common.py"
    findings: List[str] = []
    seed_confirmed = False

    if not path.exists():
        findings.append("MISSING_FILE: baselines/common.py")
        return {"seed_42_confirmed": False, "findings": findings}

    source = path.read_text(encoding="utf-8")

    # Pattern: random.Random(42)
    if re.search(r"random\.Random\(\s*42\s*\)", source):
        seed_confirmed = True
        findings.append("PASS: bootstrap uses random.Random(42) in baselines/common.py")
    else:
        findings.append("FAIL: random.Random(42) NOT found in baselines/common.py — bootstrap seed unconfirmed")

    # Count bootstrap iterations
    bs_iter_match = re.search(r"for _ in range\((\d+)\)", source)
    if bs_iter_match:
        n_iter = int(bs_iter_match.group(1))
        findings.append(f"INFO: bootstrap n_iterations={n_iter} (1000 expected)")
        if n_iter < 1000:
            findings.append(f"WARN: bootstrap iterations={n_iter} < 1000; CI width may be inflated")

    return {"seed_42_confirmed": seed_confirmed, "findings": findings}


# ---------------------------------------------------------------------------
# Check 3: n_runs in b07_dynamic_v2.py — SAFEGUARD-6
# ---------------------------------------------------------------------------

def check_b07_n_runs() -> Dict[str, Any]:
    """
    SAFEGUARD-6 requires n_runs >= 5 for noise floor estimation.
    b07_dynamic_v2.py calls _runner.run(..., n_runs=1) — this is a violation.
    """
    path = REPO_ROOT / "baselines" / "v2" / "b07_dynamic_v2.py"
    findings: List[str] = []
    violation = False
    n_runs_found: Optional[int] = None

    if not path.exists():
        findings.append("MISSING_FILE: baselines/v2/b07_dynamic_v2.py")
        return {"safeguard_6_ok": False, "n_runs_found": None, "violation": True, "findings": findings}

    source = path.read_text(encoding="utf-8")

    # Find all n_runs= assignments in _runner.run() call(s)
    matches = re.findall(r"_runner\.run\([^)]*n_runs\s*=\s*(\d+)", source, re.DOTALL)
    if matches:
        n_runs_found = int(matches[0])
        if n_runs_found < 5:
            violation = True
            findings.append(
                f"SAFEGUARD-6 VIOLATION: b07_dynamic_v2.py calls _runner.run(..., n_runs={n_runs_found}). "
                f"SAFEGUARD-6 requires n_runs >= 5 for noise floor estimation. "
                f"With n_runs=1 the noise_floor_stats contain a single sample — std is always 0.0, "
                f"non_deterministic_flags will never fire, and the noise floor check is vacuous."
            )
        else:
            findings.append(f"PASS: n_runs={n_runs_found} >= 5 — SAFEGUARD-6 satisfied")
    else:
        findings.append("WARN: Could not find n_runs= pattern in _runner.run() call in b07_dynamic_v2.py")

    # Also check SandboxRunner default
    runner_path = REPO_ROOT / "sbg" / "v2" / "execution" / "runner.py"
    if runner_path.exists():
        runner_source = runner_path.read_text(encoding="utf-8")
        default_match = re.search(r"def run\s*\([^)]*n_runs\s*:\s*int\s*=\s*(\d+)", runner_source, re.DOTALL)
        if default_match:
            default_n = int(default_match.group(1))
            findings.append(f"INFO: SandboxRunner.run() default n_runs={default_n}")
            if default_n >= 5:
                findings.append("INFO: SandboxRunner default satisfies SAFEGUARD-6 (n_runs=5)")
            findings.append(
                f"NOTE: b07_dynamic_v2.py overrides the default with n_runs={n_runs_found}, "
                f"bypassing SAFEGUARD-6 noise floor check."
            )

    return {
        "safeguard_6_ok": not violation,
        "n_runs_found": n_runs_found,
        "violation": violation,
        "findings": findings,
    }


# ---------------------------------------------------------------------------
# Check 4: Anti-reproducibility patterns in source (non-benchmark)
# ---------------------------------------------------------------------------

ANTI_PATTERNS = [
    "MOCK_RESULT", "PLACEHOLDER", "FAKE_RESULT", "HARDCODED_RESULT",
    "READY_FOR_LINUX",
]

SCAN_DIRS = [
    "baselines", "sbg", "experiments", "benchmark/scripts", "phase5", "phase6", "phase7",
]

TODO_PATTERNS = ["TODO", "FIXME"]


def check_anti_patterns() -> Dict[str, Any]:
    findings: List[str] = []
    hits_critical: List[Dict[str, Any]] = []
    hits_todo: List[Dict[str, Any]] = []

    # Exclude this audit script itself to avoid self-referential pattern matches
    this_script = str(pathlib.Path(__file__).resolve().relative_to(REPO_ROOT))

    for scan_dir in SCAN_DIRS:
        dir_path = REPO_ROOT / scan_dir
        if not dir_path.exists():
            continue
        for py_file in dir_path.rglob("*.py"):
            rel = str(py_file.relative_to(REPO_ROOT))
            if rel == this_script:
                continue
            try:
                lines = py_file.read_text(encoding="utf-8").splitlines()
            except Exception:
                continue

            for lineno, line in enumerate(lines, start=1):
                # Critical patterns
                for pat in ANTI_PATTERNS:
                    if pat in line:
                        hits_critical.append({"file": rel, "line": lineno, "pattern": pat, "text": line.strip()})

                # TODO/FIXME — informational only
                for pat in TODO_PATTERNS:
                    if pat in line:
                        hits_todo.append({"file": rel, "line": lineno, "pattern": pat, "text": line.strip()})

    if hits_critical:
        for h in hits_critical:
            findings.append(f"CRITICAL_ANTI_PATTERN [{h['pattern']}] in {h['file']}:{h['line']}: {h['text']}")
    else:
        findings.append("PASS: No MOCK_RESULT / PLACEHOLDER / FAKE_RESULT / HARDCODED_RESULT / READY_FOR_LINUX found in source")

    if hits_todo:
        findings.append(f"INFO: {len(hits_todo)} TODO/FIXME comment(s) found in source (see todo_items list)")
    else:
        findings.append("PASS: No TODO/FIXME in scanned source directories")

    return {
        "critical_hits": hits_critical,
        "todo_hits": hits_todo,
        "findings": findings,
    }


# ---------------------------------------------------------------------------
# Check 5: Declared artifact hashes vs computed
# ---------------------------------------------------------------------------

def check_declared_hashes() -> Dict[str, Any]:
    """
    FINAL_REPRODUCIBILITY_MANIFEST lists 16-hex-char sha256 prefixes.
    Compare against freshly computed full sha256.
    """
    manifest_path = REPO_ROOT / "artifacts" / "final" / "FINAL_REPRODUCIBILITY_MANIFEST.json"
    findings: List[str] = []
    mismatches: List[Dict[str, str]] = []

    if not manifest_path.exists():
        findings.append("MISSING: FINAL_REPRODUCIBILITY_MANIFEST.json — cannot verify hashes")
        return {"findings": findings, "mismatches": mismatches}

    manifest = _load_json(manifest_path)
    if not manifest or "artifact_hash_manifest" not in manifest:
        findings.append("INVALID: artifact_hash_manifest key missing from manifest")
        return {"findings": findings, "mismatches": mismatches}

    for rel_path, declared_prefix in manifest["artifact_hash_manifest"].items():
        full = REPO_ROOT / rel_path
        if not full.exists():
            findings.append(f"MISSING_FOR_HASH_CHECK: {rel_path}")
            mismatches.append({"path": rel_path, "status": "FILE_MISSING"})
            continue

        actual_hex = _sha256(full)
        if actual_hex.startswith(declared_prefix):
            findings.append(f"PASS hash: {rel_path} ({declared_prefix}…)")
        else:
            mismatches.append({
                "path": rel_path,
                "declared_prefix": declared_prefix,
                "actual_prefix": actual_hex[:len(declared_prefix)],
                "status": "HASH_MISMATCH",
            })
            findings.append(
                f"HASH_MISMATCH: {rel_path}  declared={declared_prefix}  actual={actual_hex[:len(declared_prefix)]}"
            )

    return {"findings": findings, "mismatches": mismatches}


# ---------------------------------------------------------------------------
# Check 6: Seed documentation in REGISTRY.yaml
# ---------------------------------------------------------------------------

def check_registry_seeds() -> Dict[str, Any]:
    """All experiments in REGISTRY.yaml must declare seed=42."""
    path = REPO_ROOT / "experiments" / "REGISTRY.yaml"
    findings: List[str] = []
    missing_seed: List[str] = []

    if not path.exists():
        findings.append("MISSING: experiments/REGISTRY.yaml")
        return {"findings": findings, "missing_seed": missing_seed}

    source = path.read_text(encoding="utf-8")
    # Extract experiment ids and their seed declarations
    exp_ids = re.findall(r"id:\s*(EXP-\w+)", source)
    seed_vals = re.findall(r"seed:\s*(\d+)", source)

    for i, exp_id in enumerate(exp_ids):
        if i < len(seed_vals):
            seed_val = int(seed_vals[i])
            if seed_val != 42:
                missing_seed.append(exp_id)
                findings.append(f"FAIL: {exp_id} has seed={seed_val}, expected 42")
            else:
                findings.append(f"PASS: {exp_id} seed=42")
        else:
            missing_seed.append(exp_id)
            findings.append(f"FAIL: {exp_id} has no seed declaration")

    return {"findings": findings, "missing_seed": missing_seed}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_audit() -> Dict[str, Any]:
    print("[REPRODUCIBILITY AUDIT] Starting audit…")

    artifact_check    = check_artifacts()
    bootstrap_check   = check_bootstrap_seed()
    b07_check         = check_b07_n_runs()
    anti_pattern_check = check_anti_patterns()
    hash_check        = check_declared_hashes()
    registry_check    = check_registry_seeds()

    # Aggregate violations
    all_violations: List[str] = []
    all_violations += artifact_check["violations"]
    if not bootstrap_check["seed_42_confirmed"]:
        all_violations.append("BOOTSTRAP_SEED_NOT_CONFIRMED: random.Random(42) not found in baselines/common.py")
    if b07_check["violation"]:
        all_violations.append(
            f"SAFEGUARD-6_VIOLATION: b07_dynamic_v2.py n_runs={b07_check['n_runs_found']} < 5"
        )
    all_violations += [h["text"] for h in anti_pattern_check["critical_hits"]]
    all_violations += [m["path"] + " " + m["status"] for m in hash_check["mismatches"]]
    if registry_check["missing_seed"]:
        all_violations.append(f"MISSING_SEED_DECLARATIONS: {registry_check['missing_seed']}")

    audit_result = {
        "audit_version": "v2.0",
        "agent": "Agent-N: Reproducibility Audit",
        "repo_root": str(REPO_ROOT),
        "overall_status": "FAIL" if all_violations else "PASS",
        "n_violations": len(all_violations),
        "violations": all_violations,
        "checks": {
            "artifact_existence_and_keys": artifact_check,
            "bootstrap_seed": bootstrap_check,
            "b07_safeguard_6": b07_check,
            "anti_patterns": anti_pattern_check,
            "declared_hash_verification": hash_check,
            "registry_seeds": registry_check,
        },
    }

    # Write output
    AUDIT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_OUT, "w", encoding="utf-8") as fh:
        json.dump(audit_result, fh, indent=2)

    # Print summary
    print(f"\n[REPRODUCIBILITY AUDIT] Overall status: {audit_result['overall_status']}")
    print(f"[REPRODUCIBILITY AUDIT] Violations found: {len(all_violations)}")
    for v in all_violations:
        print(f"  ⚠  {v}")
    print(f"\n[REPRODUCIBILITY AUDIT] Full results written to: {AUDIT_OUT}")

    return audit_result


if __name__ == "__main__":
    result = run_audit()
    sys.exit(0 if result["overall_status"] == "PASS" else 1)
