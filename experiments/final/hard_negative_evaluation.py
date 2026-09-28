"""
experiments/final/hard_negative_evaluation.py
=============================================
Runs the SBG V5 distance on the 12 hard-negative pairs.

What was wrong before
---------------------
``benchmark/v5/hard_negatives/oracle.py`` reports a column headed "Oracle"
whose value is computed as::

    outputs_match = (base_result == variant_result) and (base_exc == variant_exc)

That is an output comparison. It never computes an SBG distance. The README
nevertheless reported its 12/12 score under the heading "Behavioral oracle",
attributing an output-reading result to the output-free representation.

This script computes the actual SBG V5 distance and applies the pre-fixed
decision threshold tau* = 0.08 (the median SBG distance of semantics-preserving
dev pairs, fixed before the hard negatives were scored and not re-tuned here).
The output comparison is retained, relabelled as what it is: an output-reading
reference that bounds what any output-free method could achieve on this set.

Two input regimes are reported, both fixed in advance:

  canonical  the 11 protocol inputs, so the numbers are comparable with the
             main benchmark
  declared   each pair's own ``TEST_INPUTS``, which the benchmark ships as part
             of the pair definition and which were written to expose the
             semantic difference

Neither regime is selected after seeing scores; both are reported.

Output: artifacts/final/HARD_NEGATIVE_V5_RESULTS.json
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import types
from typing import Any, Dict, List, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sbg.statistics import wilson_interval                      # noqa: E402
from sbg.v2.execution.runner import SandboxRunner               # noqa: E402
from sbg.v3.genome import DynamicGenomeExtractorV3, distance_v3  # noqa: E402
from sbg.v5.state_transition_genome import StateTransitionGenome  # noqa: E402
from sbg.v5.temporal_genome_v5 import distance as temporal_distance  # noqa: E402
from sbg.v5.temporal_genome_v5 import extract as extract_temporal    # noqa: E402
from experiments.final.extraction import CANONICAL_INPUTS, W_STATE, W_TEMPORAL, W_V3  # noqa: E402

PAIRS_DIR = REPO_ROOT / "benchmark" / "v5" / "hard_negatives"
TAU_STAR = 0.08          # pre-fixed; see docstring. Never re-tuned in this file.
SEED = 42

_runner = SandboxRunner()
_extractor = DynamicGenomeExtractorV3()
_state = StateTransitionGenome()


def _load(pair_dir: pathlib.Path, filename: str) -> types.ModuleType:
    path = pair_dir / filename
    spec = importlib.util.spec_from_file_location(f"{pair_dir.name}_{filename[:-3]}", path)
    module = importlib.util.module_from_spec(spec)          # type: ignore[arg-type]
    spec.loader.exec_module(module)                          # type: ignore[union-attr]
    return module


def _genomes(module: types.ModuleType, program_id: str, inputs: List[Any]):
    result = _runner.run(program_id, module.run, inputs, n_runs=5, seed=SEED,
                         max_events=5000)
    genome = _extractor.extract_from_traces(program_id, result.traces)
    flat, events = [], []
    for run in result.traces:
        for trace in run:
            flat.append(trace)
            for event in trace.events:
                events.append({"event_type": event.event_type,
                               "function_name": event.function_name,
                               "depth": getattr(event, "depth", 0)})
    try:
        temporal = extract_temporal(events, program_id=program_id)
    except Exception:                                        # noqa: BLE001
        temporal = None
    try:
        state = _state.extract(flat)
    except Exception:                                        # noqa: BLE001
        state = None
    return genome, temporal, state


def _distance_v5(a, b) -> Dict[str, float]:
    g1, t1, s1 = a
    g2, t2, s2 = b
    d_v3 = distance_v3(g1, g2)
    d_temporal = temporal_distance(t1, t2) if (t1 and t2) else d_v3
    d_state = _state.distance(s1, s2) if (s1 and s2) else d_v3
    full = (t1 is not None and t2 is not None and s1 is not None and s2 is not None)
    d_v5 = (W_V3 * d_v3 + W_TEMPORAL * d_temporal + W_STATE * d_state) if full else d_v3
    return {"sbg_v5": round(min(1.0, max(0.0, d_v5)), 6),
            "sbg_v3": round(d_v3, 6),
            "temporal": round(d_temporal, 6),
            "state": round(d_state, 6),
            "exception_component": round(
                0.5 * (0.0 if not (set(g1.exception_type_set) | set(g2.exception_type_set))
                       else 1.0 - len(set(g1.exception_type_set) & set(g2.exception_type_set))
                       / len(set(g1.exception_type_set) | set(g2.exception_type_set)))
                + 0.5 * abs(g1.exception_rate - g2.exception_rate), 6),
            "v5_full": full}


def _output_reference(base_mod, variant_mod, inputs) -> Dict[str, Any]:
    """Output-reading reference. NOT an SBG result; reported as a ceiling."""
    def call(mod):
        try:
            return mod.run(inputs), None
        except Exception as exc:                             # noqa: BLE001
            return None, f"{type(exc).__name__}: {exc}"
    base_result, base_exc = call(base_mod)
    variant_result, variant_exc = call(variant_mod)
    identical = (base_result == variant_result) and (base_exc == variant_exc)
    return {"reads_program_output": True,
            "predicted": "EQUIV" if identical else "CHANGED"}


def evaluate(regime: str) -> Dict[str, Any]:
    pair_dirs = sorted(d for d in PAIRS_DIR.iterdir()
                       if d.is_dir() and d.name.startswith("pair_"))
    rows = []
    for pair_dir in pair_dirs:
        metadata = json.loads((pair_dir / "metadata.json").read_text())
        base_mod = _load(pair_dir, "base_program.py")
        variant_mod = _load(pair_dir, "variant_program.py")
        declared = _load(pair_dir, "test_inputs.py").TEST_INPUTS

        inputs = CANONICAL_INPUTS if regime == "canonical" else [declared]
        row: Dict[str, Any] = {
            "pair_id": pair_dir.name,
            "ground_truth": metadata["ground_truth"],
            "ground_truth_label": 1 if metadata["ground_truth"] == "CHANGED" else 0,
            "shortcut_defeated": metadata["shortcut_defeated"],
            "input_regime": regime,
            "n_inputs": len(inputs),
            "threshold_tau_star": TAU_STAR,
            "base_program": str((pair_dir / "base_program.py").relative_to(REPO_ROOT)),
            "variant_program": str((pair_dir / "variant_program.py").relative_to(REPO_ROOT)),
        }
        try:
            base = _genomes(base_mod, pair_dir.name + "_base", inputs)
            variant = _genomes(variant_mod, pair_dir.name + "_variant", inputs)
            distances = _distance_v5(base, variant)
            row["trace_status"] = "ok"
            row["distances"] = distances
            row["sbg_v5_predicted"] = "CHANGED" if distances["sbg_v5"] > TAU_STAR else "EQUIV"
            row["sbg_v3_predicted"] = "CHANGED" if distances["sbg_v3"] > TAU_STAR else "EQUIV"
            row["exception_predicted"] = (
                "CHANGED" if distances["exception_component"] > TAU_STAR else "EQUIV")
        except Exception as exc:                             # noqa: BLE001
            row["trace_status"] = "failed"
            row["trace_failure"] = f"{type(exc).__name__}: {exc}"
            row["sbg_v5_predicted"] = None

        row["output_reference"] = _output_reference(base_mod, variant_mod, declared)
        rows.append(row)

    def confusion(key: str) -> Dict[str, Any]:
        tp = fp = tn = fn = unscored = 0
        for row in rows:
            predicted = (row.get(key) if key != "output_reference"
                         else row["output_reference"]["predicted"])
            truth = row["ground_truth"]
            if predicted is None:
                unscored += 1
                continue
            if truth == "CHANGED" and predicted == "CHANGED":
                tp += 1
            elif truth == "CHANGED":
                fn += 1
            elif predicted == "CHANGED":
                fp += 1
            else:
                tn += 1
        n = tp + fp + tn + fn
        precision = tp / (tp + fp) if (tp + fp) else None
        recall = tp / (tp + fn) if (tp + fn) else None
        f1 = (2 * precision * recall / (precision + recall)
              if precision and recall else 0.0 if (precision is not None and recall is not None)
              else None)
        accuracy = (tp + tn) / n if n else None
        return {
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "n_scored": n, "n_unscored": unscored,
            "precision": round(precision, 4) if precision is not None else None,
            "recall": round(recall, 4) if recall is not None else None,
            "f1": round(f1, 4) if f1 is not None else None,
            "accuracy": round(accuracy, 4) if accuracy is not None else None,
            "accuracy_95ci_wilson": wilson_interval(tp + tn, n) if n else None,
        }

    return {
        "input_regime": regime,
        "n_pairs": len(rows),
        "threshold_tau_star": TAU_STAR,
        "threshold_provenance": (
            "median SBG distance of semantics-preserving dev pairs; fixed before "
            "these pairs were scored and not re-tuned here"
        ),
        "metrics": {
            "sbg_v5_output_free": confusion("sbg_v5_predicted"),
            "sbg_v3_output_free": confusion("sbg_v3_predicted"),
            "exception_component_output_free": confusion("exception_predicted"),
            "output_reading_reference": confusion("output_reference"),
        },
        "pairs": rows,
    }


def main() -> int:
    payload = {
        "experiment": "HARD_NEGATIVE_V5_EVALUATION",
        "supersedes": "benchmark/v5/hard_negatives/oracle.py summary table",
        "correction": (
            "The 12/12 figure previously reported as a behavioural-oracle result "
            "is an output comparison. It is reported here as "
            "'output_reading_reference' and is not an SBG result."
        ),
        "seed": SEED,
        "regimes": {},
    }
    for regime in ("canonical", "declared"):
        print(f"[hard-negatives] regime={regime}", flush=True)
        payload["regimes"][regime] = evaluate(regime)
        metrics = payload["regimes"][regime]["metrics"]
        for name, m in metrics.items():
            print(f"    {name:34s} acc={m['accuracy']} "
                  f"TP={m['tp']} FP={m['fp']} TN={m['tn']} FN={m['fn']}", flush=True)

    out = REPO_ROOT / "artifacts" / "final" / "HARD_NEGATIVE_V5_RESULTS.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
