"""Writes artifacts/final/FREEZE_V8_AMENDMENT1.json (see the 'reason' field). Reads no scores."""
import datetime
import hashlib
import json
import pathlib

R = pathlib.Path(__file__).resolve().parents[2]
sha = lambda p: hashlib.sha256((R / p).read_bytes()).hexdigest()   # noqa: E731
fz = json.loads((R / "artifacts/final/FREEZE_V8.json").read_text())
ABORT = "artifacts/final/ABORTED_v8test_attempt1_checkpoint_500rows_NOT_USED.jsonl"
am = {
    "artifact": "FREEZE_V8_AMENDMENT1", "status": "FROZEN",
    "written_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "amends": {"file": "artifacts/final/FREEZE_V8.json", "sha256": sha("artifacts/final/FREEZE_V8.json"),
               "freeze_commit": "ebb8c44e161b00b95e039fe0cf45e0a7690d9eee"},
    "reason": ("First test scoring attempt (full 1130-pair file, PYTHONHASHSEED=0) stalled at pair 526 "
               "(test__math_gcd_lcm__sp-1_s0) at 100% CPU for >8 min; a second attempt that resumed from the checkpoint "
               "stalled at the same pair. math_gcd_lcm is one of the 8 stale-variant programs already EXCLUDED by the "
               "pre-declared rule in FREEZE_V8.json. Each of those pairs run in isolation completes, so the stall depends on "
               "accumulated tracer state (leaked non-terminating worker threads, as documented in extraction.py), not on the "
               "pair itself."),
    "aborted_runs": {
        "checkpoint_moved_aside_unread": ABORT, "checkpoint_sha256": sha(ABORT),
        "statement": ("The 500-row checkpoint written by the aborted attempt was moved aside without being opened; no score "
                      "from it was inspected, aggregated or used. It is not an input to any reported number. Row count was "
                      "read from the file size via line count only; pair ids of the next pairs were read from the "
                      "DATASET pair file, not from scores."),
        "logs": ["artifacts/paper_evidence/logs/v8test_attempt1_aborted.txt",
                 "artifacts/paper_evidence/logs/v8test_attempt2_aborted.txt"]},
    "disclosure": ("While diagnosing the stall, one tool call printed rows[-1]['pair_id'] and the count of the checkpoint, and a "
                   "probe script re-extracted three math_power_modular and two math_gcd_lcm pairs in isolation printing only "
                   "ok/failure_kind. No SBG score of a test pair was printed or computed."),
    "change": [
        "Test scoring runs on artifacts/final/v8_test_nonstale/pairs_test.jsonl = benchmark/datasets/v8/pairs_test.jsonl "
        "minus the pairs of the 4 pre-declared stale test programs (967 pairs, 22 programs). The filter is by program name "
        "from DIAGNOSTIC_V8_STALE_VARIANTS.json; no score was read.",
        "evaluate_v8.py: FREEZE path now FREEZE_V8_AMENDMENT1.json; the pair-id completeness assertion applies to non-stale "
        "pairs only. Dev numbers are unchanged (dev dry-run re-run is identical)."],
    "effect_on_estimand": ("None. The evaluated set is exactly the set the freeze defined after the pre-declared exclusion; "
                           "only the 163 excluded pairs are no longer traced."),
    "evaluation_script_sha256": sha("experiments/final/evaluate_v8.py"),
    "test_pair_file": {"path": "artifacts/final/v8_test_nonstale/pairs_test.jsonl",
                       "sha256": sha("artifacts/final/v8_test_nonstale/pairs_test.jsonl")},
    "code_sha256_now": {p: sha(p) for p in fz["code_sha256"]},
    "run_command": ("PYTHONHASHSEED=0 venvs/py313/bin/python experiments/final/run_main_evaluation.py --split test "
                    "--protocol output_free_v8 --dataset-dir artifacts/final/v8_test_nonstale --tag v8test "
                    "--out-dir artifacts/final --checkpoint-every 25"),
}
am["frozen_code_files_changed_since_freeze"] = [
    p for p, h in fz["code_sha256"].items() if am["code_sha256_now"][p] != h]
(R / "artifacts/final/FREEZE_V8_AMENDMENT1.json").write_text(json.dumps(am, indent=2) + "\n")
print("changed frozen code files:", am["frozen_code_files_changed_since_freeze"])
