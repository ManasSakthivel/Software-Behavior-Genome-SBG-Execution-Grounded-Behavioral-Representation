# Superseded hard-coded gate (historical record, do not cite)

`final_stanford_gate.py.txt` and `FINAL_STANFORD_GATE.json.txt` are verbatim
copies of `experiments/final/final_stanford_gate.py` and
`artifacts/final/FINAL_STANFORD_GATE.json` from commit `657281b`
(2026-09-28). The script **hard-codes every category as PASS** and its verdict
string (all twenty categories PASS, "PUBLICATION READY") from prose, with no computation from
artifacts. Its own docstring states "All categories PASS because ...". It was
removed in commit `ad7b655` and replaced by the evidence-driven
`experiments/final/stanford_gate.py`.

The copies are `.txt` so they cannot be executed or picked up as code. They are
kept only so the history of that claim is visible in the working tree. The
verdict they contain is **not supported by any evidence in this repository**.
