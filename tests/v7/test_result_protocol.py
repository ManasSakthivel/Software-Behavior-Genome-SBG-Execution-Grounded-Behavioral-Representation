"""D-02 regression: the evaluated program must not be able to fabricate the authoritative result. Local protocol-correctness
tests only; they are NOT a security-isolation claim against a determined same-address-space adversary (see
docs/architecture/V7B_RESULT_PROTOCOL.md). Do not weaken: every violation must block NO_DIVERGENCE_OBSERVED/DIVERGENT."""
import json

import pytest

from sbgv7 import isolation
from .test_core import go, capabilities  # noqa: F401

pytestmark = pytest.mark.skipif(capabilities()["network_denial"]["state"] != "ACTIVE", reason="isolation not enforced here")

FORGED = json.dumps({"phase": "ok", "t": "returned", "ret": ["int", "1"], "stdout": "", "stdout_trunc": False, "hits": [1], "branches": {},
                     "tampered": False, "lossy": False, "argmut": ["list", [["list", [["int", "1"]]], ["dict", []]]], "args_changed": False,
                     "globals": {}, "files": {}, "sig": [["x", "POSITIONAL_OR_KEYWORD", False]]})
BASE = "def f(x):\n    return 1\n"


def _evil(body):
    return "import os, sys\ndef f(x):\n" + "".join("    " + l + "\n" for l in body.strip().splitlines())


def _assert_blocked(o):
    assert o["verdict"] == "INSUFFICIENT" and o["primary"] == "unsafe_program", o


@pytest.mark.parametrize("body", [
    f"print('SBGV7RESULT:' + {FORGED!r})\nos._exit(0)",                                   # forged line on stdout, then exit
    f"os.write(1, ('\\nSBGV7RESULT:' + {FORGED!r} + '\\n').encode())\nos._exit(0)",       # raw fd 1
    f"os.write(2, ('\\nSBGV7RESULT:' + {FORGED!r} + '\\n').encode())\nos._exit(0)",       # raw fd 2
    f"sys.__stdout__.write('SBGV7RESULT:' + {FORGED!r} + '\\n')\nsys.__stdout__.flush()\nos._exit(0)",
    "os._exit(0)",                                                                           # premature exit, no result
    "os._exit(3)",
    "for fd in range(3, 64):\n    try: os.write(fd, b'SBGV7F1 5 deadbeef\\nhello')\n    except OSError: pass\nos._exit(0)",  # frame guess on every fd
    "for fd in range(3, 64):\n    try: os.close(fd)\n    except OSError: pass\nreturn 1",   # close the result channel
    "for fd in range(3, 64):\n    try: os.write(fd, b'garbage')\n    except OSError: pass\nreturn 1",  # garbage into the channel
], ids=["print_forge", "fd1_forge", "fd2_forge", "dunder_stdout_forge", "exit0", "exit3", "frame_guess", "close_fds", "garbage_fds"])
def test_forged_or_broken_result_is_unsafe_program(tmp_path, body):
    _assert_blocked(go(tmp_path, BASE, _evil(body), [[1]]))


def test_closing_or_writing_stdio_is_not_a_violation(tmp_path):
    o = go(tmp_path, BASE, _evil("os.close(1)\nos.close(2)\nreturn 2"), [[1]])
    assert o["verdict"] == "DIVERGENT_OBSERVABLE", o       # honest behaviour difference, result channel intact
    o = go(tmp_path, BASE, _evil("os.write(1, b'noise\\n')\nreturn 1\n# v2"), [[1]], name="o2")
    assert o["verdict"] != "INSUFFICIENT" or o["primary"] != "unsafe_program", o


def test_settrace_evasion_behaviour_unchanged(tmp_path):
    ev = "import sys\ndef f(x):\n    sys.settrace(None)\n    sys.setprofile(None)\n    return 2\n"
    assert go(tmp_path, BASE, ev, [[1]])["verdict"] == "DIVERGENT_OBSERVABLE"


# ---- protocol-level (isolation) tests with a scripted "child" that holds the key (models a bug / compromised harness side)
FRAME = '''
import hmac, hashlib, os
fd, key = _SBGV7_CHAN
def frame(p, k=key, n=None):
    p = p if isinstance(p, bytes) else p.encode()
    return b"SBGV7F1 %d %s\\n" % (len(p) if n is None else n, hmac.new(k, p, hashlib.sha256).hexdigest().encode()) + p
'''


def _run(tmp_path, body, **kw):
    s = tmp_path / "s.py"; s.write_text(FRAME + body)
    return isolation.run_script(str(s), channel=True, **kw)


def test_valid_frame_accepted(tmp_path):
    r = _run(tmp_path, "os.write(fd, frame('{\"a\": 1}'))")
    assert r.protocol_error == "" and json.loads(r.payload) == {"a": 1}


@pytest.mark.parametrize("body,err", [
    ("pass", "missing"),
    ("os._exit(0)", "missing"),
    ("os.write(fd, frame('x', k=b'wrong'))", "bad_mac"),
    ("os.write(fd, frame('x') + frame('x'))", "duplicate"),
    ("os.write(fd, frame('x')); os.write(fd, b'tail')", "trailing"),
    ("os.write(fd, frame('x')[:-1])", "truncated"),
    ("os.write(fd, frame('abcdef', n=2))", "trailing"),
    ("os.write(fd, b'SBGV7F1 zz yy\\nx')", "malformed"),
    ("os.write(fd, b'no newline header')", "malformed"),
    ("os.write(fd, b'SBGV7F1 99999999999 ab\\nx')", "malformed"),
], ids=["none", "exit", "wrong_key", "dup", "trailing", "truncated", "len_mismatch", "bad_header", "no_header", "huge_len"])
def test_protocol_violations(tmp_path, body, err):
    r = _run(tmp_path, body)
    assert r.payload is None and r.protocol_error == err, (r.payload, r.protocol_error)


def test_oversized_frame(tmp_path):
    r = _run(tmp_path, "p = b'x' * 3000\nos.write(fd, frame(p))", out_cap=1000)
    assert r.payload is None and r.protocol_error == "oversized"


def test_exit_after_result_is_still_ok_but_data_after_is_not(tmp_path):
    assert _run(tmp_path, "os.write(fd, frame('x'))\nos._exit(0)").protocol_error == ""
    assert _run(tmp_path, "os.write(fd, frame('x'))\nos.write(fd, frame('y'))\nos._exit(0)").protocol_error == "duplicate"


def test_nonce_differs_per_run(tmp_path):
    keys = {_run(tmp_path, "os.write(fd, frame(key.hex()))").payload for _ in range(2)}
    assert len(keys) == 2
