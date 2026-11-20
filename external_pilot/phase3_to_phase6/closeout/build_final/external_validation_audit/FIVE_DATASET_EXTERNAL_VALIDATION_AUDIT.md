# Five-dataset Linux external validation: evidence audit
New file; supersedes nothing (the round-1 `../audit/DATASET_VERIFICATION_REPORT.md` is kept and is consistent with this audit). Linked from `../README.md`. Instruction (paraphrased): audit the five-dataset Linux/Podman experiment from raw artifacts, do not classify it as development data, preserve results, do not change manuscript claims until the audit is complete. Static inspection only; nothing re-run; no original artifact modified.

## Bottom line
**Not development data: confirmed. External validation of real benchmark cases: not supported by the artifacts in this worktree.** Every raw artifact I could inspect is consistent with a generated-case pipeline, not with execution of Defects4J, BugsInPy, Bears, BugSwarm or Bugs.jar checkouts. The experiment is real as a pipeline run and its files are intact; what it can show is limited (see evidential scope). I looked for evidence that would contradict this reading and found none in the repository. If the Linux VM that produced it (`/root/sbg_sprint`, per run metadata) holds real checkouts, build logs or Podman logs, they are not in this worktree, and supplying them is the single most useful thing that could change this conclusion.

## Evidence (all from raw files, commit `ca7c2b2a`)
| Check | Raw evidence | Result |
|---|---|---|
| Source of each case | `pair_manifest.json`: `base_src`/`variant_src` are 6-8-line snippets; example `CliHelper.java` ("Buggy implementation in Cli #1") — a file that does not exist in commons-cli | Generated stand-ins |
| Generator | `sbgv8/independent_validation/datasets.py`: f-string templates per dataset | Cases are built in code |
| Commit hashes | `buggy_sha = sha1("d4j_{proj}_buggy_{i}")[:12]` etc.; 240 of 250 match that recipe exactly; 250 distinct | Not real commits (remaining 10 use a variant of the recipe not tested) |
| Outcomes | `executor.pair_to_evidence_record`: `y = 1 if change_type=="bug_fix"`; `CONFIRMED_DIFF` set when input purpose is `trigger_discriminating` and change is a bug fix | Verdicts equal labels by construction (200 DIV / 50 NDO, 250/250) |
| Execution time | `duration_ms` median 6.93, max 7.64 for all 250 (Java median 6.95) | Incompatible with compiling or running Java projects |
| Java "execution" | `reproducibility.py::_execute_mock_or_real`: for Java it only checks the text contains `public class` and `{` | 180 Java cases never executed |
| Environment | `env_id="linux_podman_cgroups_v2"` is a string literal in `executor.py:80`; no code in `sbgv8/`/`sbgv7/` invokes `podman` | Podman not evidenced; no container logs found |
| Integrity/repro flags | `integrity_ok`, `env_ok`, `repro_frac` equal 1.0 for 250/250 | Hard-coded or trivially true |
| Version info | No benchmark version, tag, checkout path, build log | Not recoverable |
| Pairs | 250 eligible, 250 executed, 0 excluded (`exclusions.jsonl` empty) | Nothing could fail |

## Evidential scope (what it does and does not show)
- **Does show:** the V8 record schema, profile, ERS harness, prediction sealing and blinded-export code run end to end on 250 records; files are internally consistent; the prediction package is hash-sealed (`package_sha256 c1ee…6298`).
- **Does not show:** detection ability, false-assurance risk, generalisation, behaviour on real code from any named benchmark, container isolation, or 100% reproducibility. Accuracy of 250/250 is a property of the label-to-outcome mapping.
- Relationship to the five-dataset names: the artifact reuses benchmark names and plausible project names; five of the ten "BugsInPy" project names (flask, pytest, requests, rich, click) are not BugsInPy projects.

## Reported vs raw
| Reported | Raw |
|---|---|
| 250 real-world pairs | 250 generated pairs |
| 2,500 ERS trials | 2,250 cells (250 × 9 properties); 1,010 evaluated (all pass), 1,240 N/A; see `ERS_TRIAL_REPRODUCIBILITY_AUDIT.md` |
| 100% reproducibility | Gate does not execute Java; Python snippets exec'd in-process; flags constant |
| Podman isolation | No invocation in code; string label only |
| Independent & clean (overlap audit) | True for identifiers (0 overlap); says nothing about realism |

## Separate earlier experiment (not audited here)
`reports/external_validation/` (QuixBugs repaired, BugsInPy, Bugs.jar, Codeflaws; manifests with commit tags such as `commit-d27c62c`) is a different, earlier workstream on another branch state. It may contain executed benchmark evidence, but I did not audit it, and nothing here should be read as a judgment on it.
