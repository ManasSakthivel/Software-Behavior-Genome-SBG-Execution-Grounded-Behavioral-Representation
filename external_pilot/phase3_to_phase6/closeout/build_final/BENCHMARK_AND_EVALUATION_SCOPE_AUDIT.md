# Benchmark and evaluation scope audit
Supersedes nothing; linked from README.md. Source: `datasets/v8/dev_records.jsonl`, `realexec_matrix.json`, `audit/DATASET_VERIFICATION_REPORT.md`.

| Cat. | Setting | Subjects | Executed | Ground truth | Independent |
|---|---|---|---|---|---|
| A | Synthetic pairs | 150 (101 programs) | Yes | Generator labels | No |
| A | QuixBugs buggy/fixed + negatives | 31 + 85 (31 programs) | Yes | Benchmark tests / by construction | No |
| A | BugsInPy units | 46 (43 bugs, 12 projects) | Yes | None (unlabelled) | No |
| B | Real-execution P2/P5/P6 | 30 pairs, 720 trials (macOS, dirty tree) | Yes | Label-free | No |
| C | Cross-platform analysis | 312 records | Yes | - | - |
| D | Attacks/probes | 25 macOS, 125 Linux | Yes | Designed | No |
| E | Tests | 257 | Yes | Assertions | No |
| F | Five-dataset artifact | 250 | **No** | Labels copied | Excluded |
| G | Adjudication | - | **No** | - | Planned |

All Python, development-exposed. Breadth score 3/10 (up from 2 only because executed evidence was under-reported; no new evidence). Never five benchmark executions.
