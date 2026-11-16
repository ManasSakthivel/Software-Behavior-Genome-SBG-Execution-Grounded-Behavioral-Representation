# Workstream 3: Freeze and SHA-256 Provenance Audit

**Audit Date:** 2026-11-07  
**Artifacts Inspected:** `artifacts/final/FREEZE_*.json`, `artifacts/final/freeze_*.json`  
**Auditor Mode:** Read-only byte verification  

---

## 1. Executive Summary

All committed freeze manifests and hash chains were audited by direct SHA-256 computation of disk files. 

1. **`FREEZE_V10.json` (Pre-execution Freeze):**  
   All **25 of 25 tracked code, model, and dataset files** match their committed SHA-256 hashes exactly. Zero hash mismatches.
2. **`FREEZE_V10_SCORED.json` (Post-execution Freeze):**  
   The raw scored output file `artifacts/final/pairs_v10_test_v6exp.jsonl` matches the registered hash `292233fe70000b8f60326da2e2a22b9a0613caa95d5cd5c186ee9e3f01e2d146` byte-for-byte.
3. **`FREEZE_V9.json`:**  
   All 12 code and model dependencies match their frozen SHA-256 hashes.
4. **`FREEZE_V8.json` & Amendments 1–2:**  
   The two pre-execution amendments to the chunked test harness (`evaluate_v8.py`) are fully tracked in `FREEZE_V8_AMENDMENT1.json` and `FREEZE_V8_AMENDMENT2.json`, and match the current script hash (`34f303af...`).
5. **External Benchmark Freezes:**  
   `freeze_bugsinpy.json` (256/256 file hashes verified) and `freeze_quixbugs.json` maintain unbroken cryptographic integrity.

---

## 2. Table of Verified Hashes (FREEZE_V10)

| Relative Path | Expected SHA-256 (from Manifest) | Actual SHA-256 on Disk | Status |
|---|---|---|---|
| `experiments/final/evaluate_v10.py` | `11f13de1e3bdbf3e929556ed9c0fb541314c19bc59164fc654d84e747038bbc5` | `11f13de1e3bdbf3e929556ed9c0fb541314c19bc59164fc654d84e747038bbc5` | **MATCH** |
| `experiments/final/evaluate_v4_dev.py` | `c3f2b1997e2aa2540cee30c2392c51224a122e6f966e74f6fb83ec7af00f69a8` | `c3f2b1997e2aa2540cee30c2392c51224a122e6f966e74f6fb83ec7af00f69a8` | **MATCH** |
| `experiments/final/evaluate_v9.py` | `096e030a8d184a64e6c0c4fde065ce9001a147be016b262413064c30e83958dc` | `096e030a8d184a64e6c0c4fde065ce9001a147be016b262413064c30e83958dc` | **MATCH** |
| `artifacts/final/V10_MODELS_FROZEN.json` | `fe637cbddd0236086e964f7c2b609ad4c6c0af72322733dfecd8cada287f7e76` | `fe637cbddd0236086e964f7c2b609ad4c6c0af72322733dfecd8cada287f7e76` | **MATCH** |
| `benchmark/datasets/v10_independent/pairs_test.jsonl` | `476c3efffcf4a20c9cf92212b932b03b29c64ca8e505742710a0da7555d53735` | `476c3efffcf4a20c9cf92212b932b03b29c64ca8e505742710a0da7555d53735` | **MATCH** |
| `benchmark/datasets/v10_independent/manifest.json` | `488b45f102632524e318054ae8c9ab421c206be79110ffcca4cf3bad6bd429f4` | `488b45f102632524e318054ae8c9ab421c206be79110ffcca4cf3bad6bd429f4` | **MATCH** |
| `sbg/v6/state_transition_genome_v6.py` | `c99b26d667c1b27ae13f90df75fba76326f1be5ed91c25f3138704bebdc5ae28` | `c99b26d667c1b27ae13f90df75fba76326f1be5ed91c25f3138704bebdc5ae28` | **MATCH** |
| `experiments/final/score_v6_experimental.py` | `fe1f0dbbab8655217c4c75fe7430d0ffbbff6970bab85386e6ea523e1c1d134f` | `fe1f0dbbab8655217c4c75fe7430d0ffbbff6970bab85386e6ea523e1c1d134f` | **MATCH** |
| `experiments/final/extraction.py` | `549d5cf29acb807e9b984e40c424f730744ab01d2642bd7fc2d24008f1835f55` | `549d5cf29acb807e9b984e40c424f730744ab01d2642bd7fc2d24008f1835f55` | **MATCH** |
| `experiments/final/protocol.py` | `b121d9c73174117b6c943c348e92311a6ac4d60c03b799aeffbc24714accfdab` | `b121d9c73174117b6c943c348e92311a6ac4d60c03b799aeffbc24714accfdab` | **MATCH** |
| `experiments/final/entry_policy.py` | `4514383f432e65d9f7e695b49e2c9f6ce79581099f05b94952e6dff6e1e437ea` | `4514383f432e65d9f7e695b49e2c9f6ce79581099f05b94952e6dff6e1e437ea` | **MATCH** |
| `experiments/final/class_driver.py` | `f426edac1e6c68e22b8d89816ad80876a55b488fafa3c65cf44daaa29ddec093` | `f426edac1e6c68e22b8d89816ad80876a55b488fafa3c65cf44daaa29ddec093` | **MATCH** |
| `experiments/final/static_baselines.py` | `0facb27875ac1ae00d75a56e48b8412cfbadd67b21e587160083a2cb0e8001df` | `0facb27875ac1ae00d75a56e48b8412cfbadd67b21e587160083a2cb0e8001df` | **MATCH** |
| `experiments/final/edit_size_analysis.py` | `f5957c6da488f91f983a35fb102f35752a67fb9ea1cb7c12f30d86169967da9e` | `f5957c6da488f91f983a35fb102f35752a67fb9ea1cb7c12f30d86169967da9e` | **MATCH** |
| `experiments/final/fit_weights.py` | `af15680c43ba93b1e4d9badcfe965f5368193975dd6399bdaef4d08c6015de34` | `af15680c43ba93b1e4d9badcfe965f5368193975dd6399bdaef4d08c6015de34` | **MATCH** |
| `sbg/statistics.py` | `727519b47b1aa1142172817ed4b9a67ad42817e49d9ad4a187fc3f8b59d3924b` | `727519b47b1aa1142172817ed4b9a67ad42817e49d9ad4a187fc3f8b59d3924b` | **MATCH** |
| `sbg/extraction/dynamic/tracer.py` | `76676e91725142aac4314a52f005ea1494f43e3385ac42bd810a9fd7e4fced6f` | `76676e91725142aac4314a52f005ea1494f43e3385ac42bd810a9fd7e4fced6f` | **MATCH** |
| `sbg/v3/genome.py` | `8cc7437bdc6323ac9b7ff6b917ff96b5165d1b18a896ed13524649a856f0bafe` | `8cc7437bdc6323ac9b7ff6b917ff96b5165d1b18a896ed13524649a856f0bafe` | **MATCH** |
| `sbg/v5/state_transition_genome.py` | `d098fbb71669ed4065f2ebe06f086de278fcd1ef0a70f1c25aeff7120a905f90` | `d098fbb71669ed4065f2ebe06f086de278fcd1ef0a70f1c25aeff7120a905f90` | **MATCH** |
| `sbg/v5/temporal_genome_v5.py` | `7d8b60fcc98c5ffffd83b8f32a6666bef6a8559204cf33592eb680997e76223e` | `7d8b60fcc98c5ffffd83b8f32a6666bef6a8559204cf33592eb680997e76223e` | **MATCH** |
| `benchmark/scripts/generate_v10_independent.py` | `68da1b354de0656f48ae6885b23c2e2445033c20b2750609549319aa5c326684` | `68da1b354de0656f48ae6885b23c2e2445033c20b2750609549319aa5c326684` | **MATCH** |
| `artifacts/final/pairs_v9c_train_v6exp.jsonl` | `515eceee0e371842aa8df308a85dd0638e0883792d540cef1843b3e03b02724e` | `515eceee0e371842aa8df308a85dd0638e0883792d540cef1843b3e03b02724e` | **MATCH** |
| `artifacts/final/pairs_v9c_dev_v6exp.jsonl` | `16502e7199aa11d9d7c7a77c554d634dcc2030d91a0c5b7aef3bf7e96098fb0d` | `16502e7199aa11d9d7c7a77c554d634dcc2030d91a0c5b7aef3bf7e96098fb0d` | **MATCH** |
| `artifacts/paper_evidence/V4_DEV_EVALUATION.json` | `da89b0f819e638056be127a67883d345bfe78c5a8f8dce49f5da95956fc5b115` | `da89b0f819e638056be127a67883d345bfe78c5a8f8dce49f5da95956fc5b115` | **MATCH** |
| `artifacts/paper_evidence/SBG_V6_EXPERIMENTAL_RATIONALE.md` | `9dfab9b961a9dd27fa7c5fe57e167e177a15953936fb1ace3be6b77c2e22532a` | `9dfab9b961a9dd27fa7c5fe57e167e177a15953936fb1ace3be6b77c2e22532a` | **MATCH** |

---

## 3. Single-Run Enforcement

The evaluation script `experiments/final/evaluate_v10.py` contains hardcoded hash validation that prevents execution if any underlying model, split file, or extraction logic diverges from `FREEZE_V10.json`. Once scored, the output hash is sealed in `FREEZE_V10_SCORED.json`. No subsequent parameter tuning or re-running occurred.
