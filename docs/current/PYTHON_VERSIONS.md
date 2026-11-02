# Supported Python versions

* **Canonical: Python 3.13** (`.python-version`). Every committed artifact and
  the 657-test baseline come from 3.13.
* **Supported floor: Python 3.9.** CI runs 3.9 and 3.13. After the stdlib fix in
  `external_bugsinpy.py`, the full suite passes on both.
* `artifacts/final/PYTHON_VERSION_SENSITIVITY.json` shows distance values change
  between 3.9.6 and 3.13.15 (largest observed change 0.41). Results must only be
  compared across, not mixed within, an interpreter version. A 3.9 run is a
  test of the code, not a reproduction of the artifacts.
* `make setup` hard-codes `python3.13`.

Observed example: `sort_heapsort` under `output_free_v6` yields 8771 events on
3.13 and 8024 on 3.9 (measured in this remediation; the event stream differs
between interpreter line-tracing implementations). `tests/` therefore pin the
8771 figure only on 3.13.
