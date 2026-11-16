#!/usr/bin/env python3
"""WP-D / D1 -- sandboxed child: run ONE program file on the SBG protocol inputs and print a JSON observation record.

Mirrors the V10 label oracle (SBG/benchmark/scripts/generate_v10_independent.py::oracle): per input
(status, repr(return)[:400], repr(args-after-call)[:400], stdout[:200]) with SIGALRM time-outs.  Differences from that
oracle (all disclosed in FINDINGS.md): 1.0 s per input (= SBG's per-trace budget; V10 oracle used 2.0 s) and a class-tier
branch (SBG class driver `drive`, which by construction returns None, so only exception / stdout are observable).

Safety: executed only on vendored, statically-screened files copied under WP_D/.../unit_copies; cwd = fresh temp dir;
RLIMIT_CPU/FSIZE; sockets and subprocess creation are replaced by raising stubs; stdin closed; PYTHONDONTWRITEBYTECODE=1.

usage: d1_exec_child.py canonical <file>
       d1_exec_child.py declared  <file> <entry-name> <inputs.json>
env:   D1_SBG_REPO = path of the (read-only) SBG checkout, used ONLY to import entry_policy / class_driver
"""
import contextlib
import copy
import importlib.util
import io
import json
import os
import pathlib
import re
import resource
import signal
import sys
import tempfile
import types

REPO = pathlib.Path(os.environ["D1_SBG_REPO"])
PER_INPUT_S = 1.0


class _Timeout(Exception):
    pass


def _alarm(*_):
    raise _Timeout()


def _lock_down():
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_FSIZE, (10_000_000, 10_000_000))
    import socket
    import subprocess

    def _deny(*a, **k):
        raise PermissionError("D1 sandbox: network/process creation disabled")
    socket.socket = _deny
    socket.create_connection = _deny
    socket.getaddrinfo = _deny
    subprocess.Popen = _deny
    os.system = _deny
    sys.stdin = open(os.devnull)


_ADDR = re.compile(r"0x[0-9a-fA-F]+")


def _obs(fn, inp, mode):
    args = copy.deepcopy(inp)
    buf = io.StringIO()
    signal.setitimer(signal.ITIMER_REAL, PER_INPUT_S)
    try:
        with contextlib.redirect_stdout(buf):
            if mode == "class":
                r = fn(args)
            elif mode == "declared":
                r = fn(*args)
            elif args is None or args == [None]:
                r = fn()
            elif isinstance(args, tuple):
                r = fn(*args)
            else:
                r = fn(args)
        return ["ok", _ADDR.sub("0x?", repr(r)[:400]), _ADDR.sub("0x?", repr(args)[:400]), buf.getvalue()[:200]]
    except _Timeout:
        return ["timeout", "", "", buf.getvalue()[:200]]
    except BaseException as exc:                                               # noqa: BLE001
        return ["exc", type(exc).__name__, _ADDR.sub("0x?", repr(args)[:400]), buf.getvalue()[:200]]
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


def emit(rec):
    sys.stdout.write("@@" + json.dumps(rec) + "\n")
    sys.stdout.flush()


def main():
    mode = sys.argv[1]
    path = pathlib.Path(sys.argv[2]).resolve()
    inputs_path = pathlib.Path(sys.argv[4]).resolve() if len(sys.argv) > 4 else None
    rec = {"file": str(path), "mode": mode, "status": None}
    sys.path.insert(0, str(REPO))
    os.chdir(tempfile.mkdtemp(prefix="d1_exec_"))
    _lock_down()
    src = path.read_text()
    try:
        compile(src, str(path), "exec")
    except SyntaxError as exc:
        rec.update(status="syntax_error", detail=f"{exc.msg} (line {exc.lineno})")
        return emit(rec)
    spec = importlib.util.spec_from_file_location("_d1_prog", str(path))
    mod = types.ModuleType("_d1_prog")
    old = signal.signal(signal.SIGALRM, _alarm)
    real_stdout = sys.stdout
    sys.stdout = io.StringIO()
    signal.setitimer(signal.ITIMER_REAL, 5.0)
    try:
        spec.loader.exec_module(mod)
    except BaseException as exc:                                               # noqa: BLE001
        sys.stdout = real_stdout
        rec.update(status="import_error", detail=f"{type(exc).__name__}: {exc}"[:300])
        return emit(rec)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        sys.stdout = real_stdout

    emode = mode
    if mode == "canonical":
        from experiments.final.entry_policy import select_entry_structural, EntryPointError
        try:
            dec = select_entry_structural(src)
            fn = getattr(mod, dec.name, None)
            inputs = dec.inputs
            rec.update(entry=dec.name, tier="function", arity=dec.arity, fully_annotated=dec.fully_annotated)
            if not callable(fn):
                rec.update(status="no_entry_function", detail="selected entry not callable at import")
                return emit(rec)
        except EntryPointError as exc:
            if exc.kind == "no_entry_function":
                from experiments.final.class_driver import select_class_entry
                fn, disc, inputs, det = select_class_entry(mod, src)
                if fn is None or inputs is None:
                    rec.update(status="unsupported_signature", detail=f"class tier: {det}"[:300])
                    return emit(rec)
                emode = "class"
                rec.update(entry=disc, tier="class")
            else:
                rec.update(status=exc.kind, detail=str(exc)[:300])
                return emit(rec)
    else:
        name = sys.argv[3]
        inputs = [tuple(a) if isinstance(a, list) else (a,) for a in json.load(open(inputs_path))]
        fn = getattr(mod, name, None)
        rec.update(entry=name, tier="declared")
        if not callable(fn):
            rec.update(status="no_entry_function", detail=f"{name} not defined")
            return emit(rec)

    out = []
    n_to = 0
    for inp in inputs:
        o = _obs(fn, inp, emode)
        out.append(o)
        if o[0] == "timeout":
            n_to += 1
    signal.signal(signal.SIGALRM, old)
    rec.update(status="ok", n_inputs=len(inputs), n_timeouts=n_to, obs=out)
    emit(rec)


if __name__ == "__main__":
    main()
    os._exit(0)
