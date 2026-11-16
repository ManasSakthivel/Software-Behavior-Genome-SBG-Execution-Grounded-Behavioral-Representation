# BLOCKED, FAILED, INTERRUPTED AND UNVERIFIED WORK

| # | Item | Type | Cause / evidence | Continuation |
|---|---|---|---|---|
| 1 | `math_gray_code` trace dump (v9c_train) | FAILED rc=-9 after 1057 s | killed (likely memory/OOM or runaway tracing); never investigated; `logs/EXP-ORCH-003_v9c_train.log` | WP-E: run ONE bounded subprocess with RSS watchdog (kill >6 GB, wall ≤300 s): `PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 $PY experiments/common/dump_traces.py --design v9c --split train --worker math_gray_code --outdir /tmp/mgc_probe` ; inspect program (events cap? infinite loop variant?). Until resolved: exclude from trace-based train fits and say so; do not silently drop |
| 2 | First trace-dump launch died with shell | INTERRUPTED (resolved) | nohup in non-detached tool call; relaunched with `background:true` | none |
| 3 | Predecessor A4 run | INTERRUPTED/UNKNOWN PROVENANCE | cancelled 20:04; whether held-out labels were joined before freeze (20:02:54) unknown; `stages_eval.py` edited 20:04:50 after freeze | WP-A (A4R): classify; reproduce under new IDs |
| 4 | A4R deliverables | NOT DELIVERED so far | agent active, no `EXP-A4R-001/VERIFIED_BASELINES.json`; A4C apparently proceeded with its own modules (`a4c_methods.py`) without it — **protocol risk**: confirm A4C used no UNVERIFIED predecessor module on held-out data | WP-A/WP-B reconcile |
| 5 | A4C/A4B/A4D registries | MISSING | no `A4*.jsonl` files yet | each agent (or WP owner) must write registry before finishing |
| 6 | Held-out benchmark predictions | NOT YET EXISTING | only v9c_train/v9c_dev predictions | WP-B |
| 7 | A5 (ablation, state-genome dominance, SC-6/return-value, external validation, version/event-cap/timeout sensitivity) | NOT STARTED | spawn attempts reported cancelled; no files | WP-C, WP-D |
| 8 | A6 adversarial review, AJ positioning/readiness, AI artifact manifest, EXP-ORCH-006 | NOT STARTED | – | WP-F, WP-E |
| 9 | Kessel & Atkinson full text | BLOCKED (external) | no legitimate open copy | any Kessel baseline must be labelled ADAPTED from abstract+thesis |
| 10 | Python-version portability | KNOWN LIMITATION | results valid only on CPython 3.13.x | disclose; A5G quantifies AUROC effect |
| 11 | V9c-val label noise | KNOWN DATA DEFECT | 16/216 EQUIV changed output; 67/216 CHANGED unobservable | report clean-subset sensitivity; do not alter labels |
| 12 | Spawn-tool "cancelled" messages | TOOLING | agents ran anyway | verify by mtimes |
| 13 | py39 pytest SIGABRT (`math_fib_matrix`) | informational | 758 passed before abort | none |
| 14 | `FREEZE_V10.variants_tree_sha256` unreproducible | open | algorithm undocumented | A3/A2 note; low impact |
| 15 | ORCH-006 SBG tree re-hash after A4 wave | NOT RUN | – | WP-E (last) |
| 16 | A4-wave worry: output-reading baselines on the protocol's inputs are label-tautological | design risk | A1 finding; A4B/A4C plan labels them oracle-ceiling vs independent-input variant | A4D must verify independence of the "independent" battery (not overlapping the 11 protocol inputs; no label access) before any superiority/inferiority claim |
