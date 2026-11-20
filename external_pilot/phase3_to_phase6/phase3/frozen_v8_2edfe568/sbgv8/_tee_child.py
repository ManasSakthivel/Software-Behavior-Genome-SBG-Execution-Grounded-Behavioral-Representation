"""V8 child wrapper (runs ONLY under sbgv8.procsep.Supervisor, via sbgv7._child -> runpy). It runs the UNMODIFIED sbgv7/harness.py but
makes every write the program sends to sys.stdout also reach the parent on the REAL fd 2 as framed tee records, BEFORE the harness's
own Cap object sees it. A program that patches Cap.write (attack A08) therefore still leaves an independent record the parent compares
with the harness-reported stdout. argv = [this, harness_json_arg, run_nonce].
This is NOT isolation from the evaluated program: it shares the address space, so code that replaces sys.stdout / contextlib.redirect_stdout /
os.write itself, or dup2()s fd 2, can still forge or suppress records (it can at worst make the record INCOMPLETE, which the parent treats as
untrusted). Wire format: b"@@SBGV8T@@<nonce32> <seq> <O|W|X|C> <hex>@@\\n"."""
import contextlib, os, runpy, sys

_arg, _nonce = sys.argv[1], sys.argv[2].encode()
_chan = globals().pop("_SBGV7_CHAN")
_harness = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sbgv7", "harness.py")
_write, _real_exit, _redirect = os.write, os._exit, contextlib.redirect_stdout
CAP, PIECE = 1 << 18, 4096  # tee at most CAP chars (the harness keeps 32768); the final C record states the true total
_st = {"seq": 0, "chars": 0, "sent": 0, "over": False}


def _emit(kind, payload=b""):
    line = b"@@SBGV8T@@%s %d %s %s@@\n" % (_nonce, _st["seq"], kind, payload.hex().encode())
    _st["seq"] += 1
    try:
        while line:
            line = line[_write(2, line):]
    except OSError:
        pass  # the sequence number advanced, so the parent sees a gap / a missing close


class Tee:
    def __init__(self, c): self._c = c

    def write(self, s):
        if isinstance(s, str):
            _st["chars"] += len(s)
            for i in range(0, len(s), PIECE):
                p = s[i:i + PIECE]
                if _st["sent"] + len(p) > CAP:
                    p = p[:max(0, CAP - _st["sent"])]
                    if not _st["over"]: _st["over"] = True; _emit(b"X")
                if p: _st["sent"] += len(p); _emit(b"W", p.encode("utf-8", "surrogatepass"))
        return self._c.write(s)  # the harness's Cap (or whatever the program made of it) sees the write only after the record left

    def __getattr__(self, n): return getattr(self._c, n)


def _exit(code=0):
    _emit(b"C", str(_st["chars"]).encode())
    _real_exit(code)


_emit(b"O")
os._exit = _exit
contextlib.redirect_stdout = lambda c: _redirect(Tee(c))
sys.argv = [_harness, _arg]
runpy.run_path(_harness, init_globals={"_SBGV7_CHAN": _chan}, run_name="__main__")
