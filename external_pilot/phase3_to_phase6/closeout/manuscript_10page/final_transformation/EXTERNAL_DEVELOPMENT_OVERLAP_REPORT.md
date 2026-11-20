# External vs development overlap (all cohorts)
New file; linked from `../README.md`. Cohorts: V8 dev corpus (312 records), earlier external workstream, five-dataset generated run.

| Level | Earlier workstream vs V8 dev | Five-dataset vs V8 dev |
|---|---|---|
| Repository/project | QuixBugs: same repository. BugsInPy: same catalogue (commit `11c5f1ee`) | 0 project-name overlap |
| Pair/bug | QuixBugs 31 of 40 programs in dev; BugsInPy 43 of 51 eligible bugs in dev (the other 8 and 9 QuixBugs programs not found in dev) | 0 |
| Commit | BugsInPy buggy/fixed commits identical for the 43 | 0 (and not real commits) |
| Source fingerprint | Not computed: V8 dev records store evidence, not source; the earlier trees are not in the worktree. QuixBugs/BugsInPy unit sources exist locally in `external/` and could be hashed against the dev inputs in a follow-up | Not feasible |
| Bugs.jar, Codeflaws | No overlap by name | No overlap |

**Reading.** The "unseen" 8 BugsInPy bugs and 9 QuixBugs programs are classed `UNCERTAIN`: same projects and the same method family as development, case not seen in V8 dev, but the earlier workstream's tuning touched all 40 QuixBugs programs. Per-case classes are in the registry. Evidence for no `EXTERNAL_EVALUATION` class: none of the 115 entries is real, executed with V8, unseen, and untuned.
