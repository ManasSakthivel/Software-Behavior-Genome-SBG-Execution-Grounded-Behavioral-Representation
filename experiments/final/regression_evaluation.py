"""
experiments/final/regression_evaluation.py
==========================================
Runs the SBG V5 distance on the 15-pair regression corpus.

What was wrong before
---------------------
``experiments/v5/regression_evaluator.py`` reports a number it calls the
"output-free SBG distance", computed as::

    0.50 * exception_fraction_dist + 0.30 * exception_type_jaccard + 0.20 * volume_ratio

That is not the SBG representation. It contains no call-transition bigrams, no
coverage, no temporal genome and no state-transition genome -- it is three
scalar summary statistics, one of which (wall-time ratio) is not even
deterministic. Attributing its 3/15 to SBG understates the representation in
the same way that attributing the output oracle's 14/15 to SBG overstated it.

This script computes the real V5 distance
``0.50*d_v3 + 0.25*d_temporal + 0.25*d_state`` on the same 15 pairs with the
same pre-fixed threshold tau* = 0.08 and the same pre-declared trigger inputs.
The output oracle is retained and labelled as an output-reading reference.

Output: artifacts/final/REGRESSION_V5_RESULTS.json
"""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any, Dict, List

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmark.v5.regression.regression_pairs import REGRESSION_PAIRS   # noqa: E402
from sbg.statistics import wilson_interval                              # noqa: E402
from sbg.v2.execution.runner import SandboxRunner                       # noqa: E402
from sbg.v3.genome import DynamicGenomeExtractorV3, distance_v3         # noqa: E402
from sbg.v5.state_transition_genome import StateTransitionGenome        # noqa: E402
from sbg.v5.temporal_genome_v5 import distance as temporal_distance     # noqa: E402
from sbg.v5.temporal_genome_v5 import extract as extract_temporal       # noqa: E402
from experiments.final.extraction import W_STATE, W_TEMPORAL, W_V3      # noqa: E402

TAU_STAR = 0.08
SEED = 42

_runner = SandboxRunner()
_extractor = DynamicGenomeExtractorV3()
_state = StateTransitionGenome()


def _profile(fn, program_id: str, trigger_inputs: List[tuple]):
    wrapped = lambda args: fn(*args)                       # noqa: E731
    result = _runner.run(program_id, wrapped, trigger_inputs, n_runs=5, seed=SEED,
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
    except Exception:                                      # noqa: BLE001
        temporal = None
    try:
        state = _state.extract(flat)
    except Exception:                                      # noqa: BLE001
        state = None
    return genome, temporal, state, len(events)


def _output_reference(pair: Dict[str, Any]) -> Dict[str, Any]:
    """Output-reading reference. Reported as a ceiling, never as SBG.

    Two definitions are reported because the superseded artifact used the
    narrower one and the difference is worth a line rather than a footnote:

    return_value_only   compares returned values; an input on which both
                        versions raise counts as agreement, which is how
                        artifacts/v5/REGRESSION_EVALUATION_RESULTS.json
                        reached 14/15
    full_behaviour      compares returned values AND raised exception types
    """
    n_diff_full = n_diff_return = 0
    for inputs in pair["trigger_inputs"]:
        def call(fn):
            try:
                return ("ok", fn(*inputs))
            except Exception as exc:                       # noqa: BLE001
                return ("exc", type(exc).__name__)
        buggy, fixed = call(pair["buggy_fn"]), call(pair["fixed_fn"])
        if buggy != fixed:
            n_diff_full += 1
        buggy_value = buggy[1] if buggy[0] == "ok" else None
        fixed_value = fixed[1] if fixed[0] == "ok" else None
        if buggy_value != fixed_value:
            n_diff_return += 1
    n = len(pair["trigger_inputs"])
    return {"reads_program_output": True,
            "output_divergence_full_behaviour": round(n_diff_full / n, 4),
            "output_divergence_return_value_only": round(n_diff_return / n, 4),
            "predicted_changed": n_diff_full > 0,
            "predicted_changed_return_value_only": n_diff_return > 0}


def main() -> int:
    rows = []
    for pair in REGRESSION_PAIRS:
        row: Dict[str, Any] = {
            "id": pair["id"],
            "name": pair["name"],
            "bug_type": pair["bug_type"],
            "ground_truth_label": 1,          # every pair is a genuine bug/fix pair
            "n_trigger_inputs": len(pair["trigger_inputs"]),
            "bug_visible_to_exception": pair["bug_visible_to_exception"],
            "bug_visible_to_volume": pair["bug_visible_to_volume"],
            "threshold_tau_star": TAU_STAR,
        }
        try:
            g1, t1, s1, n_events_buggy = _profile(pair["buggy_fn"], pair["id"] + "_buggy",
                                                  pair["trigger_inputs"])
            g2, t2, s2, n_events_fixed = _profile(pair["fixed_fn"], pair["id"] + "_fixed",
                                                  pair["trigger_inputs"])
            d_v3 = distance_v3(g1, g2)
            d_temporal = temporal_distance(t1, t2) if (t1 and t2) else d_v3
            d_state = _state.distance(s1, s2) if (s1 and s2) else d_v3
            full = all(x is not None for x in (t1, t2, s1, s2))
            d_v5 = (W_V3 * d_v3 + W_TEMPORAL * d_temporal + W_STATE * d_state) if full else d_v3
            exc_union = set(g1.exception_type_set) | set(g2.exception_type_set)
            exc_jaccard = (0.0 if not exc_union else
                           1.0 - len(set(g1.exception_type_set) & set(g2.exception_type_set))
                           / len(exc_union))
            row["trace_status"] = "ok"
            row["n_events_buggy"] = n_events_buggy
            row["n_events_fixed"] = n_events_fixed
            row["distances"] = {
                "sbg_v5": round(min(1.0, max(0.0, d_v5)), 6),
                "sbg_v3": round(d_v3, 6),
                "temporal": round(d_temporal, 6),
                "state": round(d_state, 6),
                "exception_component": round(
                    0.5 * exc_jaccard + 0.5 * abs(g1.exception_rate - g2.exception_rate), 6),
                "v5_full": full,
            }
            row["detected_by_sbg_v5"] = d_v5 > TAU_STAR
            row["detected_by_sbg_v3"] = d_v3 > TAU_STAR
            row["detected_by_exception_component"] = (
                row["distances"]["exception_component"] > TAU_STAR)
        except Exception as exc:                           # noqa: BLE001
            row["trace_status"] = "failed"
            row["trace_failure"] = f"{type(exc).__name__}: {exc}"
            row["detected_by_sbg_v5"] = None
        row["output_reference"] = _output_reference(pair)
        row["is_silent_bug"] = not (pair["bug_visible_to_exception"]
                                    or pair["bug_visible_to_volume"])
        rows.append(row)

    def rate(key: str, subset=None) -> Dict[str, Any]:
        selected = [r for r in rows if subset is None or subset(r)]
        scored = [r for r in selected if r.get(key) is not None]
        detected = sum(1 for r in scored if r[key])
        n = len(scored)
        return {
            "n_total": len(selected),
            "n_scored": n,
            "n_unscored": len(selected) - n,
            "n_detected": detected,
            "detection_rate": round(detected / n, 4) if n else None,
            "detection_rate_95ci_wilson": wilson_interval(detected, n) if n else None,
        }

    silent = lambda r: r["is_silent_bug"]                   # noqa: E731
    payload = {
        "experiment": "REGRESSION_V5_EVALUATION",
        "supersedes": "artifacts/v5/REGRESSION_EVALUATION_RESULTS.json",
        "correction": (
            "The superseded artifact's 'sbg_distance_output_free' was a three-statistic "
            "proxy, not the SBG V5 representation; its 'output_oracle_BASELINE' 14/15 was "
            "reported in the README as an SBG result. Both are corrected here."
        ),
        "seed": SEED,
        "threshold_tau_star": TAU_STAR,
        "n_pairs": len(rows),
        "all_pairs": {
            "sbg_v5_output_free": rate("detected_by_sbg_v5"),
            "sbg_v3_output_free": rate("detected_by_sbg_v3"),
            "exception_component_output_free": rate("detected_by_exception_component"),
            "output_reading_reference_full_behaviour": {
                "n_total": len(rows),
                "n_detected": sum(1 for r in rows if r["output_reference"]["predicted_changed"]),
                "detection_rate": round(
                    sum(1 for r in rows if r["output_reference"]["predicted_changed"])
                    / len(rows), 4),
                "note": "reads program outputs; a ceiling, not an SBG result",
            },
            "output_reading_reference_return_value_only": {
                "n_total": len(rows),
                "n_detected": sum(1 for r in rows
                                  if r["output_reference"]["predicted_changed_return_value_only"]),
                "detection_rate": round(
                    sum(1 for r in rows
                        if r["output_reference"]["predicted_changed_return_value_only"])
                    / len(rows), 4),
                "note": "definition used by the superseded artifact",
            },
        },
        "silent_bugs_only": {
            "definition": "bug invisible to both the exception and the volume shortcut",
            "sbg_v5_output_free": rate("detected_by_sbg_v5", silent),
            "output_reading_reference": {
                "n_total": sum(1 for r in rows if r["is_silent_bug"]),
                "n_detected": sum(1 for r in rows
                                  if r["is_silent_bug"]
                                  and r["output_reference"]["predicted_changed"]),
                "note": "reads program outputs; a ceiling, not an SBG result",
            },
        },
        "pairs": rows,
    }

    out = REPO_ROOT / "artifacts" / "final" / "REGRESSION_V5_RESULTS.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")

    for name, block in payload["all_pairs"].items():
        print(f"  {name:34s} {block.get('n_detected')}/{block.get('n_scored', block.get('n_total'))}"
              f"  rate={block.get('detection_rate')}")
    sb = payload["silent_bugs_only"]
    print(f"  silent bugs: SBG V5 {sb['sbg_v5_output_free']['n_detected']}"
          f"/{sb['sbg_v5_output_free']['n_scored']}   "
          f"output reference {sb['output_reading_reference']['n_detected']}"
          f"/{sb['output_reading_reference']['n_total']}")
    print(f"wrote {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
