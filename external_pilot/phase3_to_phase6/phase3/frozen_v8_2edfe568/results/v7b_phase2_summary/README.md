# V7-B Phase 2 experiment summaries (exploratory, non-pristine data)
Compact, tracked subset of the local experiment outputs E1 and E3-E7 (2026-11-18, engine commit `a6afa639` unless the RUN_RECORD says otherwise).
Included: processed per-pair files, statistics CSV/JSON, run logs, RUN_RECORD.md, command scripts, E7 verification tables and the consolidated tables.
NOT included (too large; ~470 MB, about 27,000 files): the raw per-run evidence directories (`raw/`, `V*/raw`, `S2F*/raw`, `work/`, `corruption/`).
They are preserved in tar.gz archives outside the repository at `~/Desktop/SBG-V6-phase2-raw-archive/` and identified by the sha256 sums in `RAW_ARCHIVE_SHA256SUMS.txt`; they are also on disk in gitignored `results/repro/p2_*` of the working machine.
Historical V5/V6/V7 results elsewhere under `results/` are untouched. The directory `results/phase2/` belongs to the older programme and is not used here.
