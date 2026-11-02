"""Writes artifacts/final/FREEZE_V8_AMENDMENT2.json (harness-only change). Reads no test scores."""
import datetime
import hashlib
import json
import pathlib

R = pathlib.Path(__file__).resolve().parents[2]
sha = lambda p: hashlib.sha256((R / p).read_bytes()).hexdigest()   # noqa: E731
am = {
    "artifact": "FREEZE_V8_AMENDMENT2", "status": "FROZEN",
    "written_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "amends": {"file": "artifacts/final/FREEZE_V8_AMENDMENT1.json", "sha256": sha("artifacts/final/FREEZE_V8_AMENDMENT1.json")},
    "reason": ("A THIRD single-process test scoring attempt (967 non-stale pairs, Amendment 1) also stalled at ~525 pairs at 100% CPU, "
               "this time at test__math_median_two_sorted__sc13_s1_p0, a NON-stale program. Amendment 1's attribution of the stall to "
               "the stale programs was therefore only partly right; the stall is cumulative tracer state (leaked non-terminating "
               "worker threads) in one long process, and moves between pairs. Every stalling pair completes when run alone."),
    "attempt3_checkpoint": ("/tmp/v8test_final/checkpoint_v8test_output_free_v8.jsonl (525 rows) was NEVER opened and is not an "
                            "input to anything reported; it lives outside the repository."),
    "change": ("Scoring harness only: experiments/final/run_chunked.py runs run_main_evaluation.py in a fresh subprocess per base "
               "program (PYTHONHASHSEED=0) and merges rows in dataset order. No extraction, protocol, scoring, weight, threshold, "
               "metric or evaluation code is changed; evaluate_v8.py is byte-identical to the Amendment 1 hash."),
    "equivalence_check_on_dev": {
        "command": ("python experiments/final/run_chunked.py --split dev --pairs-dir benchmark/datasets/v8 --tag v8dev_chunked "
                    "--verify-against artifacts/final/pairs_v8devrescore_output_free_v8.jsonl --out-dir /tmp/chunk_dev"),
        "result": "597 pairs, 593 evaluated, 0 differ in evaluated flag or any execution score vs the single-process dev re-score",
        "note": "Dev only. Done before test was scored."},
    "evaluation_script_sha256": sha("experiments/final/evaluate_v8.py"),
    "run_chunked_sha256": sha("experiments/final/run_chunked.py"),
    "test_pair_file": {"path": "artifacts/final/v8_test_nonstale/pairs_test.jsonl", "sha256": sha("artifacts/final/v8_test_nonstale/pairs_test.jsonl")},
    "run_command": ("venvs/py313/bin/python experiments/final/run_chunked.py --split test --pairs-dir artifacts/final/v8_test_nonstale "
                    "--tag v8test --out-dir artifacts/final   # then: evaluate_v8.py run --split test"),
    "rule": "Single run. If it fails to finish, report the blocker; do not re-run after seeing scores.",
}
a1 = json.loads((R / "artifacts/final/FREEZE_V8_AMENDMENT1.json").read_text())
assert a1["evaluation_script_sha256"] == am["evaluation_script_sha256"], "evaluate_v8.py changed"
(R / "artifacts/final/FREEZE_V8_AMENDMENT2.json").write_text(json.dumps(am, indent=2) + "\n")
print("ok")
