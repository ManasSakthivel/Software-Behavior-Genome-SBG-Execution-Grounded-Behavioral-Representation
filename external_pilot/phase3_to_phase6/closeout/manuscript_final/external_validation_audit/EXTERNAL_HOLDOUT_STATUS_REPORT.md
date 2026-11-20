# External holdout status
New file; linked from `../README.md`.

| Question | Answer |
|---|---|
| Is the five-dataset run development data? | No. It has no project, pair or commit overlap with the 312-record development cohort |
| Is it a valid external validation of SBG on real benchmark cases? | **No, on present evidence.** Cases are generated, outcomes come from labels, Java was not executed, Podman is not evidenced |
| Can it be retained as external validation? | Not for detection, risk or generalisation. Retain as a labelled pipeline demonstration; original files preserved |
| Is independent adjudication done? | No. The protocol, empty form and empty registry exist |
| Prediction lock | Hash-sealed (`c1ee208e…`), predictions locked before any adjudication, but predictions are label-derived |
| Protocol freeze evidence | Lock metadata only; no pre-registration of an analysis plan found |

## Gaps that cannot be closed from existing artifacts
1. Real upstream checkouts, builds and executions of the benchmark pairs (commits verified against the upstream repositories). Needs new execution.
2. Container evidence (Podman logs, image digests, host metadata) for the run, or a new run that records it.
3. Independent adjudication (blind protocol above).
4. Recovery of raw artifacts from the original Linux VM, if they exist (`/root/sbg_sprint`); this may remove gaps 1-2 without re-running anything.

## Decision pending
Per the instruction, manuscript claims have not been changed. The current manuscript text (five-dataset artifact excluded as template-generated) is **consistent** with this audit; the audit found nothing that would justify reclassifying it as external validation. Whether to revise that wording stays open until the VM artifacts (item 4) are checked.
