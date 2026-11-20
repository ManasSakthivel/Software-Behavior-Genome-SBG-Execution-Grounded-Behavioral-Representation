# V7 Execution Threat Model

Verified platform: macOS only (Darwin 25.6, CPython 3.13.15). Linux and Docker are untested (Docker daemon was down); on non-darwin the module reports network denial and write confinement UNAVAILABLE and refuses sandboxed runs (`SANDBOX_UNAVAILABLE`).

## Assets and trust
Host process and user files, the benchmark corpus and labels, other pairs' results. The program under test is treated as buggy or accidentally hostile (hangs, crashes, forks, huge output/memory, stray network/file writes). It is NOT treated as a determined adversary.

## Threats and mitigations (observed on macOS)
| Threat | Mitigation | Status |
|---|---|---|
| Hang / infinite loop | wall timeout + group SIGKILL; RLIMIT_CPU | ENFORCED |
| Host killed by `os._exit`/crash/abort | separate process | ENFORCED |
| Leftover child processes | process group kill, ESRCH verification | ENFORCED (not vs `setsid`) |
| Memory exhaustion | parent RSS polling; RLIMIT_AS | polling ENFORCED (soft); RLIMIT_AS NOT ENFORCED on macOS |
| Disk fill | RLIMIT_FSIZE; writes confined to a temp workdir | ENFORCED |
| Output flood | capped capture, kill on cap | ENFORCED |
| Network access / exfiltration | sandbox-exec `(deny network*)` | ENFORCED |
| Writing outside workdir | sandbox-exec write deny | ENFORCED |
| Fork bomb / process count | RLIMIT_NPROC | NOT ENFORCED (not applied); only wall timeout and group kill bound it |
| Reading host files/secrets | none (reads allowed); env scrubbed, HOME=workdir | NOT MITIGATED |
| Escaping via `setsid` / double fork | none | NOT MITIGATED |
| Tracer evasion (`sys.settrace(None)`) | out of scope here | NOT MITIGATED |
| Kernel/sandbox escape | none; deprecated `sandbox-exec` | out of scope |

## Required for stronger claims
Verify on Linux CI (`--network none`, cgroups, RLIMIT_AS, PID namespace) and in Docker once a daemon is available; add read confinement; add `setsid` escape detection.
