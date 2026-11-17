"""Child-side harness (runs ONLY inside sbgv7.isolation.run_script). argv[1]=JSON cfg. Emits one 'SBGV7RESULT:'
JSON line on the real stdout; the program's own stdout is captured into the observation.
Shortcut: writes via os.write(1)/subprocesses bypass capture; tamper detection is a post-run monitoring-state check."""
import contextlib, hashlib, importlib.util, inspect, io, json, os, re, sys, time, types

cfg = json.loads(sys.argv[1])
SRC, REAL_OUT, MARK = cfg["src"], sys.stdout, "SBGV7RESULT:"
STDOUT_CAP, MAXN, MAXDEPTH = 32768, 5000, 3
LOSSY = [False]
ADDR = re.compile(r"0x[0-9a-fA-F]{4,}")


def norm(s):  # normaliser N: addresses and the private workdir only
    return ADDR.sub("0xADDR", s.replace(os.getcwd(), "<WORKDIR>"))


def canon(v, d=0):
    t = type(v)
    if v is None: return ["none"]
    if t is bool: return ["bool", v]
    if t is int: return ["int", str(v)]
    if t is float: return ["float", repr(v)]
    if t is complex: return ["complex", repr(v)]
    if t is str: return ["str", v]
    if t is bytes: return ["bytes", v.hex()]
    if t in (list, tuple, set, frozenset):
        items = list(v)
        if len(items) > MAXN:
            LOSSY[0] = True; items = items[:MAXN]
        out = [canon(i, d) for i in items]
        if t in (set, frozenset): out.sort(key=lambda n: json.dumps(n))
        return [t.__name__, out]
    if t is dict:
        items = list(v.items())
        if len(items) > MAXN:
            LOSSY[0] = True; items = items[:MAXN]
        return ["dict", [[canon(k, d), canon(x, d)] for k, x in items]]
    name = f"{t.__module__}.{t.__qualname__}"
    if d >= MAXDEPTH or not hasattr(v, "__dict__"):
        LOSSY[0] = True  # depth/opaque object: only the type is compared
        return ["obj", name, [], True]
    return ["obj", name, [[canon(k, d + 1), canon(x, d + 1)] for k, x in vars(v).items()], False]


class Cap(io.StringIO):
    over = False

    def write(self, s):
        if self.tell() + len(s) > STDOUT_CAP:
            self.over = True; s = s[: max(0, STDOUT_CAP - self.tell())]
        return super().write(s)


M = sys.monitoring
TOOL, hits, branches = 3, set(), {}


def on_line(code, line):
    if code.co_filename != SRC: return M.DISABLE
    hits.add(line)


def on_branch(code, off, dest):
    if code.co_filename != SRC: return M.DISABLE
    branches.setdefault(f"{code.co_qualname}:{code.co_firstlineno}:{off}", set()).add(dest)


def finish(res, cap):
    res["stdout"], res["stdout_trunc"] = norm(cap.getvalue()), cap.over
    res["hits"] = sorted(hits)
    res["branches"] = {k: sorted(v) for k, v in branches.items()}
    res["tampered"] = M.get_tool(TOOL) != "sbgv7" or M.get_events(TOOL) != M.events.LINE | M.events.BRANCH
    res["lossy"] = LOSSY[0]
    REAL_OUT.write("\n" + MARK + json.dumps(res) + "\n"); REAL_OUT.flush()
    os._exit(0)


def main():
    cap, res = Cap(), {}
    M.use_tool_id(TOOL, "sbgv7")
    M.register_callback(TOOL, M.events.LINE, on_line); M.register_callback(TOOL, M.events.BRANCH, on_branch)
    M.set_events(TOOL, M.events.LINE | M.events.BRANCH)
    if cfg.get("ctl"):  # alternate control setting: seeded RNG + shifted clock
        import random
        random.seed(cfg["ctl"]); off = cfg["ctl"] * 1000.0
        _t, _tn = time.time, time.time_ns
        time.time = lambda: _t() + off; time.time_ns = lambda: _tn() + int(off * 1e9)
    sys.path.insert(0, os.path.dirname(SRC))
    try:
        with contextlib.redirect_stdout(cap):
            spec = importlib.util.spec_from_file_location("sbgv7_target", SRC)
            mod = importlib.util.module_from_spec(spec); sys.modules["sbgv7_target"] = mod
            spec.loader.exec_module(mod)
    except BaseException as e:
        res["phase"] = "import_error"; res["msg"] = norm(f"{type(e).__name__}: {e}")
        finish(res, cap)
    fn = getattr(mod, cfg["entry"], None)
    if not callable(fn):
        res["phase"] = "entry_missing"; finish(res, cap)
    try:
        sig = inspect.signature(fn)
        res["sig"] = [[p.name, p.kind.name, p.default is not p.empty] for p in sig.parameters.values()]
    except (TypeError, ValueError):
        res["phase"] = "entry_missing"; res["msg"] = "no signature"; finish(res, cap)
    res["phase"] = "ok"
    if cfg["mode"] == "probe": finish(res, cap)
    try:
        args, kwargs = cfg["args"], cfg["kwargs"]
        before_g = {k: json.dumps(canon(v)) for k, v in vars(mod).items()
                    if not k.startswith("__") and not callable(v) and not isinstance(v, types.ModuleType)}
        before_a = json.dumps(canon([args, kwargs]))
        with contextlib.redirect_stdout(cap):
            try:
                sig.bind(*args, **kwargs)
                bound = True
            except TypeError:
                bound = False
            if not bound:
                res["t"] = "bind_error"
            else:
                try:
                    res["t"], res["ret"] = "returned", canon(fn(*args, **kwargs))
                except SystemExit as e:
                    res["t"], res["code"] = "exited", canon(e.code)
                except BaseException as e:
                    res["t"], res["type"], res["msg"] = "raised", f"{type(e).__module__}.{type(e).__qualname__}", norm(str(e))
        res["argmut"] = canon([args, kwargs]); res["args_changed"] = json.dumps(res["argmut"]) != before_a
        after_g = {k: canon(v) for k, v in vars(mod).items()
                   if not k.startswith("__") and not callable(v) and not isinstance(v, types.ModuleType)}
        res["globals"] = {k: v for k, v in after_g.items() if json.dumps(v) != before_g.get(k)}
        files = {}
        for root, _, names in os.walk("."):
            for n in names:
                p = os.path.join(root, n); files[p] = hashlib.sha256(open(p, "rb").read()).hexdigest()
        res["files"] = files
    except BaseException as e:  # harness bug, not a program outcome
        res = {"phase": "harness_error", "msg": f"{type(e).__name__}: {e}"}
    finish(res, cap)


main()
