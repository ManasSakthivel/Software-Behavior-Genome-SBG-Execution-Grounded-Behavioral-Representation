# E1 RUN RECORD
commit: a6afa63987b8cab3114c39abc6e5d29e0fde1ebf
branch: research/v7b-final-validation
date: 2026-11-18T02:19:06Z
python: Python 3.13.15 (/Users/manassakthivel/Desktop/SBG-V6/.venv/bin/python)
os: macOS 26.7 build 25G229 arch arm64
primary child env: PYTHONHASHSEED=0 via isolation.DET_ENV (parent ENV also sets PYTHONHASHSEED=0, OMP_NUM_THREADS=1)
command: K1_RAW=results/repro/p2_e1_20261118_074906/raw K1_PROC=results/repro/p2_e1_20261118_074906/proc .venv/bin/python experiments/v7b/k1_spike.py run   (defaults: all 4 arms, --rerun 25, 4 workers)
old comparison source (read-only): results/postfix/processed/k1_spike_per_pair.jsonl (engine at commit 700532b8, child ran with -I, random hash seed)
capabilities:
{
 "platform": "darwin",
 "python": "3.13.15",
 "rlimit_cpu": "ACTIVE",
 "rlimit_as": "UNAVAILABLE",
 "rlimit_nofile": "ACTIVE",
 "rlimit_fsize": "ACTIVE",
 "rlimit_nproc": "UNAVAILABLE",
 "process_group_kill": "ACTIVE",
 "rss_watchdog": "ACTIVE",
 "network_denial": "ACTIVE",
 "write_confinement": "ACTIVE"
}
