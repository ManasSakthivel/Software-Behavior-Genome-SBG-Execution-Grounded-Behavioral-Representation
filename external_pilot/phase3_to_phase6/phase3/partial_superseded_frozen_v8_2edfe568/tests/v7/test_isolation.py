"""Bounded, safe probes of sbgv7.isolation. Temp dirs only; every probe has a short wall cap."""
import os, subprocess, sys, tempfile, textwrap, time
import pytest
from sbgv7 import isolation as iso

CAPS = iso.capabilities()
need = lambda *ks: pytest.mark.skipif(any(CAPS[k]["state"] != "ACTIVE" for k in ks), reason="NOT ENFORCED on this machine: " + ",".join(ks))


@pytest.fixture
def wd():
    d = os.path.realpath(tempfile.mkdtemp(prefix="sbgv7t_"))
    sub = os.path.join(d, "w"); os.mkdir(sub)
    yield sub
    import shutil; shutil.rmtree(d, ignore_errors=True)


def run(wd, code, **kw):
    p = os.path.join(os.path.dirname(wd), "s.py"); open(p, "w").write(textwrap.dedent(code))
    return iso.run_script(p, workdir=wd, **kw)


def test_ok_and_callable(wd):
    r = run(wd, "print('hi')")
    assert r.status == "OK" and r.stdout.strip() == "hi" and r.peak_rss_bytes > 0 and r.cleanup_verified
    open(os.path.join(os.path.dirname(wd), "m.py"), "w").write("def f(a, b):\n    return a + b\n")
    sys.path.insert(0, os.path.dirname(wd)); import m
    r = iso.run_callable(m.f, [2, 3], workdir=wd)
    assert r.status == "OK" and r.stdout.strip() == "5"


def test_spin_wall_timeout(wd):
    r = run(wd, "while True: pass", timeout_s=1, cpu_s=60)
    assert r.status == "TIMEOUT" and r.wall_s < 3 and r.cleanup_verified


def test_cpu_rlimit(wd):
    r = run(wd, "while True: pass", timeout_s=8, cpu_s=1)
    assert r.status == "RESOURCE" and "SIGXCPU" in r.detail


def test_child_process_survival(wd):
    marker = os.path.join(wd, "pid")
    r = run(wd, f"""
        import subprocess, time
        p = subprocess.Popen(['sleep', '30']); open({marker!r}, 'w').write(str(p.pid)); time.sleep(0.3)
        """, timeout_s=5)
    pid = int(open(marker).read())
    assert r.status == "OK" and r.orphans_found and r.cleanup_verified
    time.sleep(0.2)
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)  # grandchild is dead, not a survivor


def test_os_exit_does_not_kill_host(wd):
    r = run(wd, "import os; os._exit(7)")
    assert r.status == "CRASH" and r.returncode == 7


@need("network_denial")
def test_network_denied(wd):
    code = """
        import socket
        try: socket.socket().connect(('127.0.0.1', 1)); print('connected')
        except PermissionError: print('denied')
        except OSError as e: print('refused', e.errno)
        """
    assert run(wd, code).stdout.strip() == "denied"
    assert run(wd, code, sandbox=False).stdout.strip().startswith("refused")  # control: without sandbox it is only ECONNREFUSED


@need("write_confinement")
def test_write_outside_denied(wd):
    outside = os.path.join(os.path.dirname(wd), "outside.txt")
    r = run(wd, f"""
        try: open({outside!r}, 'w').write('x'); print('wrote')
        except PermissionError: print('denied')
        open('inside.txt', 'w').write('ok'); print('inside ok')
        """)
    assert r.stdout.split() == ["denied", "inside", "ok"] and not os.path.exists(outside)
    assert run(wd, f"open({outside!r}, 'w').write('x')", sandbox=False).status == "OK"  # control
    os.unlink(outside)


def test_memory_limit_200mb_or_less(wd):
    # 180MB allocation under mem_mb=100. rlimit_as is UNAVAILABLE on macOS, so this exercises the RSS watchdog.
    r = run(wd, """
        import time; b = bytearray(180 * 2**20)
        for i in range(0, len(b), 4096): b[i] = 1
        time.sleep(5)
        """, mem_mb=100, timeout_s=10)
    assert r.status == "RESOURCE" and r.detail in ("rss_watchdog", "MemoryError (rlimit_as)") and r.wall_s < 6


@need("rlimit_as")
def test_memory_rlimit_as_hard(wd):
    r = run(wd, "b = bytearray(150 * 2**20)", mem_mb=64)
    assert r.status == "RESOURCE" and "MemoryError" in r.detail


def test_output_cap(wd):
    r = run(wd, "import sys\nwhile True: sys.stdout.write('x' * 1000)", out_cap=10000, timeout_s=10)
    assert r.status == "RESOURCE" and r.detail == "output_cap" and r.stdout_truncated and len(r.stdout) == 10000


def test_sandbox_unavailable_is_explicit(wd, monkeypatch):
    monkeypatch.setattr(iso, "_CAPS", dict(CAPS, network_denial={"state": "UNAVAILABLE", "detail": "x"}))
    assert run(wd, "print(1)").status == "SANDBOX_UNAVAILABLE"


def test_no_stray_processes():
    out = subprocess.run(["ps", "-axo", "command"], capture_output=True, text=True).stdout
    import re  # anchored: unrelated shells/greps may merely mention these strings
    assert not re.search(r"^\S*python\S* -I -B \S*sbgv7/_child\.py|^sleep 30$", out, re.M)
