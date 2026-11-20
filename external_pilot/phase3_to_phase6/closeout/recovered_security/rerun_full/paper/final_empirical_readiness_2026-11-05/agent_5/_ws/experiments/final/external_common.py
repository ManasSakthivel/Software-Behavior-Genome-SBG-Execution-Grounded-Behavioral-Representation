"""
experiments/final/external_common.py
====================================
Shared machinery for the external real-program corpora (QuixBugs, BugsInPy).
Implements the common rules of docs/current/PHASE2_PREREGISTRATION.md §6.

- ``generate_sp_negatives``: makes the negatives. These are
  semantics-preserving variants of the fixed program, built with the
  repository's own SP transformers. Order SP-1, SP-2, SP-4, SP-6, SP-10, SP-3,
  SP-5, SP-9 at seed 0. The first three candidates that compile and whose
  normalised AST differs from the original are kept.
- ``hash_files`` / ``write_freeze``: freeze the manifest and the negatives
  before anything is scored.
- ``make_row``: the per-pair record schema, shared with the main evaluation.
  The fields ``evaluated``, ``label``, ``base_id`` and ``scores`` mean what they
  mean in ``experiments/final/analyse_results.py``.
- ``static_scores``: the token and AST structural baselines.
- ``analyse_rows``: produces the statistics:
  - AUROC for every predictor, with a cluster bootstrap by program;
  - within-cluster permutation, with the (b+1)/(m+1) estimator;
  - the label-shuffle noise floor for the primary predictor;
  - paired ΔAUROC of SBG V5 against the comparators, with Holm correction;
  - the detection rate and false-positive rate at the frozen τ*, each with a
    Wilson interval.
- ``read_frozen_threshold``: reads ``artifacts/final/THRESHOLD_FROZEN.json``.
  τ* is never derived from external data.

Pure Python. It runs on 3.9 and has no numpy.
"""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sbg.statistics import (                                         # noqa: E402
    auroc, cluster_bootstrap_ci, cluster_permutation_p, holm_bonferroni,
    label_shuffle_noise_floor, paired_cluster_bootstrap_delta, wilson_interval,
)
from experiments.final.static_baselines import (                     # noqa: E402
    ast_multiset, multiset_distance, token_multiset,
)

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "final"
THRESHOLD_PATH = ARTIFACT_DIR / "THRESHOLD_FROZEN.json"

SP_ORDER = ("SP-1", "SP-2", "SP-4", "SP-6", "SP-10", "SP-3", "SP-5", "SP-9")
SP_SEED = 0
N_NEGATIVES = 3

SEED = 42
N_BOOTSTRAP = 2000
N_PERMUTATIONS = 2000
N_SHUFFLES = 500

PRIMARY = "sbg_v5"
# Pre-registered Holm family for the external corpora (prereg §5/§6).
COMPARATORS = ("static_ast", "static_token", "exception_fraction", "call_count", "sbg_v3")


# ---------------------------------------------------------------------------
# Hashing / freezing
# ---------------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    return sha256_bytes(pathlib.Path(path).read_bytes())


def rel(path: pathlib.Path) -> str:
    """Repository-relative POSIX path, so artifacts carry no home directory."""
    path = pathlib.Path(path).resolve()
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def hash_files(paths: Iterable[pathlib.Path]) -> Dict[str, Any]:
    """Per-file SHA-256 plus one digest over the sorted (path, hash) list."""
    per_file = {rel(p): sha256_file(p) for p in paths}
    combined = sha256_bytes(
        "\n".join(f"{k} {v}" for k, v in sorted(per_file.items())).encode())
    return {"n_files": len(per_file), "combined_sha256": combined, "files": per_file}


def write_freeze(path: pathlib.Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")


# ---------------------------------------------------------------------------
# SP negatives
# ---------------------------------------------------------------------------

def _normalised(source: str) -> str:
    return ast.unparse(ast.parse(source))


def generate_sp_negatives(source_path: pathlib.Path, out_dir: pathlib.Path,
                          variant_prefix: str) -> Tuple[List[dict], List[dict]]:
    """Semantics-preserving negatives for one fixed program.

    Returns ``(accepted, rejected)``. Accepted entries carry the variant path;
    rejected entries carry the reason, so the generation is fully auditable.
    """
    from benchmark.transformations.preserving.transformer import apply_transformation

    source_path = pathlib.Path(source_path)
    base_source = source_path.read_text()
    base_norm = _normalised(base_source)
    out_dir.mkdir(parents=True, exist_ok=True)
    accepted: List[dict] = []
    rejected: List[dict] = []
    for kind in SP_ORDER:
        if len(accepted) >= N_NEGATIVES:
            break
        try:
            variant_source, _meta = apply_transformation(str(source_path), kind, seed=SP_SEED)
        except Exception as exc:                                   # noqa: BLE001
            rejected.append({"transformation_type": kind, "seed": SP_SEED,
                             "reason": f"generator raised: {type(exc).__name__}: {exc}"})
            continue
        try:
            compile(variant_source, "<variant>", "exec")
        except SyntaxError as exc:
            rejected.append({"transformation_type": kind, "seed": SP_SEED,
                             "reason": f"uncompilable: {exc.msg}"})
            continue
        if _normalised(variant_source) == base_norm:
            rejected.append({"transformation_type": kind, "seed": SP_SEED,
                             "reason": "no_op: normalised AST identical"})
            continue
        variant_id = f"{variant_prefix}__{kind.lower()}_s{SP_SEED}"
        variant_path = out_dir / f"{variant_id}.py"
        variant_path.write_text(variant_source)
        accepted.append({"variant_id": variant_id, "path": rel(variant_path),
                         "transformation_type": kind, "seed": SP_SEED})
    return accepted, rejected


# ---------------------------------------------------------------------------
# Per-pair record
# ---------------------------------------------------------------------------

def static_scores(base_source: str, variant_source: str) -> Dict[str, Optional[float]]:
    out: Dict[str, Optional[float]] = {}
    try:
        out["static_token"] = round(multiset_distance(token_multiset(base_source),
                                                      token_multiset(variant_source)), 9)
    except Exception:                                              # noqa: BLE001
        out["static_token"] = None
    try:
        out["static_ast"] = round(multiset_distance(ast_multiset(base_source),
                                                    ast_multiset(variant_source)), 9)
    except Exception:                                              # noqa: BLE001
        out["static_ast"] = None
    return out


def make_row(*, pair_id: str, corpus: str, base_id: str, label: int, kind: str,
             regime: str, protocol: str, base_path: str, variant_path: str,
             base_summary: Optional[dict], variant_summary: Optional[dict],
             scores: Optional[Dict[str, float]], static: Dict[str, Optional[float]],
             extra: Optional[dict] = None) -> dict:
    """One per-pair record. ``label`` is 1 for a real bug, 0 for an SP negative."""
    evaluated = scores is not None
    failure_side = failure_kind = failure_detail = None
    if not evaluated:
        for side, summary in (("base", base_summary), ("variant", variant_summary)):
            if summary is not None and not summary.get("ok", False):
                failure_side = side
                failure_kind = summary.get("failure_kind")
                failure_detail = summary.get("failure_detail")
                break
        if failure_kind is None:
            failure_kind, failure_detail = "not_scored", "scorer returned no scores"
        if failure_detail:
            failure_detail = str(failure_detail).replace(str(REPO_ROOT) + "/", "")
    merged: Dict[str, float] = dict(scores or {})
    for key, value in static.items():
        if value is not None:
            merged[key] = value
    row = {
        "pair_id": pair_id,
        "corpus": corpus,
        "base_id": base_id,
        "label": label,
        "pair_kind": kind,
        "regime": regime,
        "protocol": protocol,
        "base_path": base_path,
        "variant_path": variant_path,
        "base_entry": (base_summary or {}).get("entry_discovery"),
        "variant_entry": (variant_summary or {}).get("entry_discovery"),
        "base_stats": (base_summary or {}).get("stats"),
        "variant_stats": (variant_summary or {}).get("stats"),
        "evaluated": evaluated,
        "failure_side": failure_side,
        "failure_kind": failure_kind,
        "failure_detail": failure_detail,
        "scores": merged if evaluated else {k: v for k, v in static.items() if v is not None},
    }
    if extra:
        row.update(extra)
    return row


# ---------------------------------------------------------------------------
# Threshold
# ---------------------------------------------------------------------------

def read_frozen_threshold() -> Tuple[Optional[float], Optional[dict]]:
    """τ* frozen on dev by the threshold stage, or (None, None) if absent."""
    if not THRESHOLD_PATH.exists():
        return None, None
    payload = json.loads(THRESHOLD_PATH.read_text())
    tau = payload.get("tau_star")
    if tau is None:
        return None, payload
    return float(tau), {"path": rel(THRESHOLD_PATH),
                        "sha256": sha256_file(THRESHOLD_PATH),
                        "protocol": payload.get("protocol"),
                        "derived_on": payload.get("split") or payload.get("derived_on")}


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def _vectors(rows: Sequence[dict], predictor: str) -> Tuple[List[float], List[int], List[str]]:
    """Same encoding as analyse_results.vectors: unevaluable pairs score 0."""
    distances, labels, clusters = [], [], []
    for row in rows:
        value = row["scores"].get(predictor) if row["evaluated"] else None
        distances.append(float(value) if value is not None else 0.0)
        labels.append(int(row["label"]))
        clusters.append(row["base_id"])
    return distances, labels, clusters


def _predictor_present(rows: Sequence[dict], predictor: str) -> bool:
    return any(predictor in r["scores"] for r in rows if r["evaluated"])


def evaluate_predictor(rows: Sequence[dict], predictor: str) -> dict:
    if not rows or not _predictor_present(rows, predictor):
        return {"n": len(rows), "auroc": None, "note": "predictor absent or empty set"}
    distances, labels, clusters = _vectors(rows, predictor)
    n_pos = sum(labels)
    if n_pos == 0 or n_pos == len(labels):
        return {"n": len(rows), "auroc": None, "note": "degenerate set (single class)"}
    lower, upper, n_eff = cluster_bootstrap_ci(distances, labels, clusters,
                                               n_bootstrap=N_BOOTSTRAP, seed=SEED)
    return {
        "n": len(rows),
        "n_positive": n_pos,
        "n_negative": len(labels) - n_pos,
        "n_clusters": len(set(clusters)),
        "auroc": round(auroc(distances, labels), 6),
        "ci95_cluster_bootstrap": [lower, upper],
        "bootstrap_resamples_effective": n_eff,
        "permutation_p": round(cluster_permutation_p(
            distances, labels, clusters, n_permutations=N_PERMUTATIONS, seed=SEED), 6),
        "n_tied_at_zero": sum(1 for d in distances if d == 0.0),
    }


def threshold_metrics(rows: Sequence[dict], predictor: str, tau: float) -> dict:
    """Detection rate on positives and FPR on negatives at ``tau`` (score > tau)."""
    distances, labels, _ = _vectors(rows, predictor)
    tp = sum(1 for d, y in zip(distances, labels) if y == 1 and d > tau)
    fp = sum(1 for d, y in zip(distances, labels) if y == 0 and d > tau)
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    return {
        "tau_star": tau,
        "rule": "flag CHANGED iff distance > tau_star; unevaluable pairs score 0",
        "detected": tp, "n_positive": n_pos,
        "detection_rate": round(tp / n_pos, 6) if n_pos else None,
        "detection_wilson95": list(wilson_interval(tp, n_pos)) if n_pos else None,
        "false_positives": fp, "n_negative": n_neg,
        "false_positive_rate": round(fp / n_neg, 6) if n_neg else None,
        "fpr_wilson95": list(wilson_interval(fp, n_neg)) if n_neg else None,
    }


def paired_comparisons(rows: Sequence[dict], primary: str = PRIMARY,
                       comparators: Sequence[str] = COMPARATORS) -> dict:
    out: Dict[str, dict] = {}
    p_values: Dict[str, float] = {}
    if not _predictor_present(rows, primary):
        return {"note": "primary predictor absent"}
    d_a, labels, clusters = _vectors(rows, primary)
    if sum(labels) in (0, len(labels)):
        return {"note": "degenerate set (single class)"}
    for comparator in comparators:
        if not _predictor_present(rows, comparator):
            out[comparator] = {"note": "comparator absent"}
            continue
        d_b, _, _ = _vectors(rows, comparator)
        result = paired_cluster_bootstrap_delta(d_a, d_b, labels, clusters,
                                                n_bootstrap=N_BOOTSTRAP, seed=SEED)
        out[comparator] = result
        if result.get("p_two_sided") is not None:
            p_values[comparator] = result["p_two_sided"]
    holm = holm_bonferroni(p_values) if p_values else {}
    for comparator, adj in holm.items():
        out[comparator]["holm"] = adj
    return {"primary": primary, "family": list(comparators), "comparisons": out}


def reference_metrics(rows: Sequence[dict], field: str = "output_reference") -> Optional[dict]:
    """Detection/FPR of the output-reading reference. Never an SBG result."""
    scored = [r for r in rows if r.get(field) and r[field].get("differs") is not None]
    if not scored:
        return None
    pos = [r for r in scored if r["label"] == 1]
    neg = [r for r in scored if r["label"] == 0]
    tp = sum(1 for r in pos if r[field]["differs"])
    fp = sum(1 for r in neg if r[field]["differs"])
    return {
        "label": "OUTPUT-READING REFERENCE (compares return values; not SBG, not output-free)",
        "n_scored": len(scored),
        "detected": tp, "n_positive": len(pos),
        "detection_rate": round(tp / len(pos), 6) if pos else None,
        "detection_wilson95": list(wilson_interval(tp, len(pos))) if pos else None,
        "false_positives": fp, "n_negative": len(neg),
        "false_positive_rate": round(fp / len(neg), 6) if neg else None,
    }


def failure_ledger(rows: Sequence[dict]) -> Dict[str, int]:
    ledger: Dict[str, int] = {"evaluated": 0}
    for row in rows:
        if row["evaluated"]:
            ledger["evaluated"] += 1
        else:
            key = f"{row.get('failure_side') or 'pair'}:{row.get('failure_kind')}"
            ledger[key] = ledger.get(key, 0) + 1
    return ledger


def analyse_rows(rows: Sequence[dict], predictors: Sequence[str],
                 tau: Optional[float]) -> dict:
    """Full statistics for one regime on the ALL and EVALUABLE sets."""
    sets = {"ALL": list(rows), "EVALUABLE": [r for r in rows if r["evaluated"]]}
    out: Dict[str, Any] = {
        "set_definitions": {
            "ALL": "every pair in the frozen manifest; unevaluable pairs score 0",
            "EVALUABLE": "pairs whose two programs both executed under the protocol",
        },
        "set_sizes": {k: len(v) for k, v in sets.items()},
        "programs_per_set": {k: len({r["base_id"] for r in v}) for k, v in sets.items()},
        "failure_ledger": failure_ledger(rows),
        "sets": {},
    }
    for name, subset in sets.items():
        block: Dict[str, Any] = {
            "predictors": {p: evaluate_predictor(subset, p) for p in predictors},
        }
        if subset and _predictor_present(subset, PRIMARY):
            d, y, c = _vectors(subset, PRIMARY)
            if 0 < sum(y) < len(y):
                block["noise_floor_primary"] = label_shuffle_noise_floor(
                    d, y, c, n_shuffles=N_SHUFFLES, seed=SEED)
        block["paired_vs_primary"] = paired_comparisons(subset)
        if tau is not None:
            block["at_tau_star"] = {p: threshold_metrics(subset, p, tau)
                                    for p in (PRIMARY, "sbg_v3", "exception_component_v3")
                                    if _predictor_present(subset, p)}
        else:
            block["at_tau_star"] = {"note": "not computed: THRESHOLD_FROZEN.json absent"}
        block["output_reading_reference"] = reference_metrics(subset)
        out["sets"][name] = block
    return out
