"""Mutation-sensitivity check for the MB-16 conformance tests and the second-stage MB tests.
For each mutation: copy sbgv6/sbgv7/tests/v7 into a fresh temp dir, apply ONE text substitution to the COPY, run the named test there
(PYTHONPATH = the copy) and require it to FAIL; the unmutated copy must pass first. The repository working tree is never written.
Usage: .venv/bin/python scripts/mutation_check_mb.py [--only SUBSTRING]   (exit 0 iff every mutation is killed)"""
import os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = "tests/v7/test_conformance_gaps.py::"
S = "tests/v7/test_second_stage.py::"
# (label, file, old, new, test node id)
MUTATIONS = [
    ("MB-16 item 1  capture_truncated", "sbgv7/decide.py", 'if i.truncated: b.append(("capture_truncated"', 'if i.truncated and False: b.append(("capture_truncated"', C + "test_capture_truncated_end_to_end"),
    ("MB-16 item 2  alignment_failed", "sbgv7/runner.py", 'st.append(("alignment_failed", f"{type(e).__name__}: {e}"))', 'st.append(("unsupported_signature", f"{type(e).__name__}: {e}"))', C + "test_alignment_failed_via_static_phase"),
    ("MB-16 item 3  SystemExit code", "sbgv7/compare.py", 'if a["code"] != b["code"]: ks.add("outcome")', 'if False: ks.add("outcome")', C + "test_systemexit_code_is_compared"),
    ("MB-16 item 4  stderr excluded", "sbgv7/runner.py", "fd1 = norm_parent(r.stdout, r.workdir", "fd1 = norm_parent(r.stdout + r.stderr, r.workdir", C + "test_stderr_only_difference_is_not_observed"),
    ("MB-16 item 5  locus unlocalised", "sbgv7/records.py", 'locus="unlocalised"', 'locus="line:1"', C + "test_witness_locus_unlocalised"),
    ("MB-16 item 6  defaults table", "sbgv7/config.py", '"r_det": (3,', '"r_det": (2,', C + "test_defaults_table_item6"),
    ("MB-16 item 7  policy_below_minimum", "sbgv7/runner.py", 'return sys.platform == "darwin" or any(', 'return False and any(', C + "test_policy_below_minimum_true_on_darwin"),
    ("MB-16 item 8  FOR_ITER branch", "sbgv7/runner.py", '"POP_JUMP_IF_NOT_NONE", "FOR_ITER", "SEND"', '"POP_JUMP_IF_NOT_NONE", "SEND"', C + "test_s2_coverage_loop_for_iter"),
    ("MB-16 item 9  evidence class", "sbgv7/records.py", 'evidence_class: str = "observation"', 'evidence_class: str = "derived"', C + "test_record_kinds_have_documented_evidence_class"),
    ("MB-16 item 10 dangling ref", "sbgv7/records.py", 'if i not in recs: raise ChainError(f"dangling ref {i}")', 'if i not in recs: continue', C + "test_trace_raises_chain_error_on_dangling_ref"),
    ("MB-16 item 12 loud not skipped", "sbgv7/isolation.py", 'caps["network_denial"] = _state(o.get("net") == "denied",', 'caps["network_denial"] = _state(False,', C + "test_loud_not_skipped_sandbox_must_be_active_on_darwin"),
    ("2nd-stage env: inherit parent env", "sbgv7/isolation.py", 'return {"PATH": "/usr/bin:/bin", "HOME": workdir,', 'return {**os.environ, "PATH": "/usr/bin:/bin", "HOME": workdir,', S + "test_child_env_is_exactly_the_allowlist_and_path_is_clean[True]"),
    ("2nd-stage env: drop hash seed", "sbgv7/isolation.py", 'DET_ENV = {"PYTHONHASHSEED": "0", ', "DET_ENV = {", S + "test_child_env_is_exactly_the_allowlist_and_path_is_clean[False]"),
    ("2nd-stage: no flush of real stdout", "sbgv7/harness.py", "try: sys.__stdout__.flush()", "try: pass", S + "test_buffered_real_stdout_difference_is_observed[write]"),
    ("2nd-stage: secrets not rebound", "sbgv7/harness.py", "random._urandom = os.urandom", "pass", S + "test_alt_virtualises_secrets_and_systemrandom"),
    ("MB-07 time shift removed (env_sensitive)", "sbgv7/harness.py", "time.time = lambda: _t() + off;", "time.time = lambda: _t();", "tests/v7/test_backlog_mb.py::test_mb07_real_env_sensitive_case"),
]


def run(tmp, node):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("PYTHON", "VIRTUAL_ENV"))}
    env["PYTHONPATH"] = tmp
    p = subprocess.run([sys.executable, "-m", "pytest", node, "-q", "-x", "-p", "no:cacheprovider"], cwd=tmp, env=env, capture_output=True, text=True, timeout=300)
    return p.returncode, p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr[-200:]


def main():
    only = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--only" else ""
    survivors, rows = [], []
    for label, rel, old, new, node in MUTATIONS:
        if only and only not in label: continue
        with tempfile.TemporaryDirectory(prefix="sbgv7_mut_") as tmp:
            for d in ("sbgv6", "sbgv7", "tests/v7"):
                shutil.copytree(os.path.join(ROOT, d), os.path.join(tmp, d), ignore=shutil.ignore_patterns("__pycache__"))
            chk = subprocess.run([sys.executable, "-c", "import sbgv7; print(sbgv7.__file__)"], cwd=tmp, env={"PYTHONPATH": tmp, "PATH": os.environ["PATH"]}, capture_output=True, text=True).stdout
            assert chk.startswith(os.path.realpath(tmp)) or chk.startswith(tmp), f"copy not imported: {chk}"
            f = os.path.join(tmp, rel); src = open(f).read()
            assert src.count(old) == 1, f"{label}: pattern found {src.count(old)} times in {rel}"
            base_rc, base_line = run(tmp, node)
            open(f, "w").write(src.replace(old, new))
            mut_rc, mut_line = run(tmp, node)
        ok = base_rc == 0 and mut_rc != 0
        rows.append((label, "baseline " + base_line, "mutant " + mut_line, "KILLED" if ok else "SURVIVED/INVALID"))
        if not ok: survivors.append(label)
        print(f"{rows[-1][3]:8} {label:42} | {rows[-1][1]} | {rows[-1][2]}", flush=True)
    print(f"{len(rows) - len(survivors)}/{len(rows)} mutants killed")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
