# SBG V8 reproducibility guide (frozen commit 2edfe568)

## Environment (as used)
- macOS 26.7, arm64 (Darwin 25.6.0).
- CPython 3.13.15 in a venv created with `uv venv --python 3.13`.
- Dependencies: `SBG_V8_DEPENDENCY_LOCK.declared.txt` (test runner, pinned) and `SBG_V8_DEPENDENCY_LOCK.installed.txt` (exact installed versions, including unpinned numpy, scipy, pandas, matplotlib).

## Steps
1. Verify the snapshot is unchanged:
   `python3 -I verify_freeze.py` (expect `mismatched=0 missing=0 extra=0`, exit 0).
2. Create the venv:
   `uv venv --python 3.13 venv313 && uv pip install --python venv313/bin/python -r SBG_V8_DEPENDENCY_LOCK.declared.txt numpy==2.5.5 scipy==1.18.1 pandas==3.1.1 matplotlib==3.11.2`
3. Run the project tests from the snapshot:
   `cd frozen_v8_2edfe568 && PYTHONDONTWRITEBYTECODE=1 ../venv313/bin/python -m pytest tests -q -p no:cacheprovider`
4. Record the exit code and full log.

## Known limits
- Evaluation of external cases cannot be run: no input generator for external modules (see the protocol §4).
- Results are macOS-specific (`sandbox-exec`).
- Do not run inside the SBG-V8-LINUX source repository; use the snapshot.
