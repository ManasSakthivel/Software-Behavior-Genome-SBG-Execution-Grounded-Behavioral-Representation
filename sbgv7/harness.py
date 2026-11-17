"""Child-side harness (runs ONLY inside sbgv7.isolation.run_script(channel=True)). argv[1]=JSON cfg. The result is ONE
HMAC-authenticated frame written to a dedicated pipe fd handed in by _child.py (see isolation.parse_frame); stdout/stderr are
never protocol, the program's own stdout is captured into the observation.
Trust: this file runs in the SAME process as the evaluated program, so this is protocol correctness (naive/accidental/forged-line
output cannot fabricate a result), NOT isolation from a determined adversary that inspects harness frames/closures (Phase 3).
Scope: this is LOCAL result-channel protocol correctness (D-02), NOT operating-system isolation and not validated as such. Bytes written to the real
fd 1 (os.write, subprocesses) are not seen here; the PARENT folds them into side:stdout (MB-02, UD-3 option A). Tamper detection is a post-run check."""
import collections, contextlib, hashlib, hmac, importlib.util, inspect, io, json, os, re, sys, time, types

cfg = json.loads(sys.argv[1])
SRC = cfg["src"]
_WFD, _KEY = globals().pop("_SBGV7_CHAN")  # KeyError (=> no result, fail closed) if not launched through the channel
STDOUT_CAP, MAXN, MAXDEPTH = 32768, 5000, 3
LOSSY = [False]
ADDR = re.compile(r"0x[0-9a-fA-F]{4,}")


def norm(s):  # normaliser N1: source path/dir (MB-03; the two versions live in different files), private workdir, addresses
    for p, t in ((SRC, "<SRC>"), (os.path.dirname(SRC), "<SRCDIR>"), (os.getcwd(), "<WORKDIR>")): s = s.replace(p, t)
    return ADDR.sub("0xADDR", s)


# Canonicalisation reads values WITHOUT running user code: no property getters, __getattr__/__getattribute__, __repr__,
# __iter__/__len__/items overrides or __eq__ are invoked. Containers are read through the builtin base type's own
# unbound C methods; instance state through the type's __dict__ / slot descriptors (found by walking type.__mro__).
# Anything not read (opaque C/function/iterator objects, depth/size/node budget exceeded, unreadable descriptor)
# sets LOSSY, which blocks S2. Cycles are recorded structurally as ["cycle", stack_index] (exact, not lossy).
MAXNODES, MAXNEST = 50000, 40
_TG = type.__dict__
_name = lambda t: f"{_TG['__module__'].__get__(t)}.{_TG['__qualname__'].__get__(t)}"
_BASES = ((int, lambda v: ["int", hex(int.__add__(v, 0))]), (float, lambda v: ["float", repr(float.__add__(v, 0.0))]),
          (str, lambda v: ["str", str.__str__(v) if type(v) is str else "".join(str.__iter__(v))]),
          (bytes, lambda v: ["bytes", bytes(memoryview(v)).hex()]))
_state = {"nodes": 0}


def _attrs(v, t, d, stack):
    """[[key, canon]] of instance __dict__ then every slot of every class in the MRO; None if state was unreadable."""
    out, mro = [], _TG["__mro__"].__get__(t)
    for cls in mro:
        cd = _TG["__dict__"].__get__(cls)
        if "__dict__" in cd and isinstance(cd["__dict__"], types.GetSetDescriptorType):
            try:
                inst = cd["__dict__"].__get__(v, t)
            except Exception:
                LOSSY[0] = True; continue
            out += [[_c(k, d + 1, stack), _c(x, d + 1, stack)] for k, x in dict.items(inst)]
            break
    for cls in mro:
        sl = _TG["__dict__"].__get__(cls).get("__slots__")
        if sl is None: continue
        try:
            names = [sl] if isinstance(sl, str) else list(sl)
        except Exception:
            LOSSY[0] = True; continue
        for n in names:
            if n in ("__dict__", "__weakref__"): continue
            if n.startswith("__") and not n.endswith("__"): n = f"_{cls.__name__.lstrip('_')}{n}"
            desc = _TG["__dict__"].__get__(cls).get(n)
            if not isinstance(desc, types.MemberDescriptorType):
                LOSSY[0] = True; out.append([["str", n], ["unreadable"]]); continue
            try:
                out.append([["str", n], _c(desc.__get__(v, t), d + 1, stack)])
            except AttributeError:
                out.append([["str", n], ["unset"]])
    return out


def canon(v):
    _state["nodes"] = 0
    return _c(v, 0, [])


def _c(v, d, stack):
    t = type(v)
    if v is None: return ["none"]
    if t is bool: return ["bool", v]
    if t is int: return ["int", hex(v)]  # hex: str(int) raises past the 4300-digit limit
    if t is float: return ["float", repr(v)]
    if t is complex: return ["complex", repr(v)]
    if t is str: return ["str", v]
    if t is bytes: return ["bytes", v.hex()]
    _state["nodes"] += 1
    if _state["nodes"] > MAXNODES or len(stack) > MAXNEST:
        LOSSY[0] = True; return ["trunc"]
    if any(v is s for s in stack): return ["cycle", next(i for i, s in enumerate(stack) if s is v)]
    stack.append(v)
    try:
        return _c2(v, t, d, stack)
    finally:
        stack.pop()


def _c2(v, t, d, stack):
    exact = t in (list, tuple, set, frozenset, dict)
    if issubclass(t, dict): kind, items = "dict", list((collections.OrderedDict.items if issubclass(t, collections.OrderedDict) else dict.items)(v))
    elif issubclass(t, collections.deque): kind, items = "deque", list(collections.deque.__iter__(v))
    elif issubclass(t, list): kind, items = "list", list(list.__iter__(v))
    elif issubclass(t, tuple): kind, items = "tuple", list(tuple.__iter__(v))
    elif issubclass(t, (set, frozenset)): kind, items = "set" if issubclass(t, set) else "frozenset", list(set.__iter__(v) if issubclass(t, set) else frozenset.__iter__(v))
    else: kind = items = None
    if kind:
        if len(items) > MAXN:
            LOSSY[0] = True; items = items[:MAXN]
        if kind == "dict": body = [[_c(k, d, stack), _c(x, d, stack)] for k, x in items]
        else:
            body = [_c(i, d, stack) for i in items]
            if kind in ("set", "frozenset"): body.sort(key=lambda n: json.dumps(n))
        if exact: return [kind if kind != "dict" else "dict", body]
        extra = []
        if kind == "deque": extra = [[["str", "<maxlen>"], _c(collections.deque.maxlen.__get__(v), d, stack)]]
        if issubclass(t, collections.defaultdict):  # factory is compared by identity-name only, never called
            f = collections.defaultdict.default_factory.__get__(v)
            extra = [[["str", "<default_factory>"], ["none"] if f is None else ["factory", f"{getattr(f, '__module__', '?')}.{getattr(f, '__qualname__', type(f).__name__)}"]]]
        return ["obj", _name(t), [[["str", "<items>"], [kind, body]]] + extra + _attrs(v, t, d, stack), False]
    for base, conv in _BASES:
        if issubclass(t, base):
            return ["obj", _name(t), [[["str", "<value>"], conv(v)]] + _attrs(v, t, d, stack), False]
    if issubclass(t, type): return ["type", _name(v)]
    if _TG["__module__"].__get__(t) in ("builtins", "types") or not (_attrs_possible(t)):
        LOSSY[0] = True  # opaque (function, iterator, C object, ...): only the type is compared
        return ["obj", _name(t), [], True]
    if d >= MAXDEPTH:
        LOSSY[0] = True
        return ["obj", _name(t), [], True]
    return ["obj", _name(t), _attrs(v, t, d, stack), False]


def _attrs_possible(t):
    for cls in _TG["__mro__"].__get__(t):
        cd = _TG["__dict__"].__get__(cls)
        if cls is not object and ("__slots__" in cd or "__dict__" in cd): return True
    return False


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
    try: sys.__stdout__.flush()  # buffered writes to the REAL stdout would be lost at os._exit; flushed bytes reach fd 1, which the parent folds into side:stdout
    except BaseException: pass  # closed/broken stdout: nothing to flush, never a harness error
    res["stdout"], res["stdout_trunc"] = norm(cap.getvalue()), cap.over
    res["hits"] = sorted(hits)
    res["branches"] = {k: sorted(v) for k, v in branches.items()}
    res["tampered"] = M.get_tool(TOOL) != "sbgv7" or M.get_events(TOOL) != M.events.LINE | M.events.BRANCH
    res["lossy"] = LOSSY[0]
    body = json.dumps(res).encode()
    buf = b"SBGV7F1 %d %s\n" % (len(body), hmac.new(_KEY, body, hashlib.sha256).hexdigest().encode()) + body
    while buf:  # EBADF etc. (user closed/redirected the fd) raises -> no frame -> parent classifies protocol_error
        buf = buf[os.write(_WFD, buf):]
    os._exit(0)


def main():
    cap, res = Cap(), {}
    M.use_tool_id(TOOL, "sbgv7")
    M.register_callback(TOOL, M.events.LINE, on_line); M.register_callback(TOOL, M.events.BRANCH, on_branch)
    M.set_events(TOOL, M.events.LINE | M.events.BRANCH)
    if cfg.get("ctl"):  # alternate control setting: seeded RNG + shifted clock
        import random
        random.seed(cfg["ctl"]); off = cfg["ctl"] * 1000.0
        _t, _tn, _m, _pc = time.time, time.time_ns, time.monotonic, time.perf_counter
        time.time = lambda: _t() + off; time.time_ns = lambda: _tn() + int(off * 1e9)
        time.monotonic = lambda: _m() + off; time.perf_counter = lambda: _pc() + off
        _rng = random.Random(cfg["ctl"] * 7919); os.urandom = lambda n: _rng.randbytes(n)  # also seeds uuid4
        random._urandom = os.urandom  # secrets/SystemRandom bound the real os.urandom at import; rebind so alt runs are seeded too (primary runs keep real entropy)
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
                    if not k.startswith("__") and not callable(v) and not issubclass(type(v), types.ModuleType)}
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
                    rv = fn(*args, **kwargs); res["t"] = "returned"
                except SystemExit as e:
                    rv = e.code; res["t"] = "exited"
                except BaseException as e:
                    res["t"], res["type"], res["msg"] = "raised", f"{type(e).__module__}.{type(e).__qualname__}", norm(str(e))
        # canonicalisation runs outside the program try: a failure here is a harness error, never a program outcome (MB-01)
        if res["t"] == "returned": res["ret"] = canon(rv)
        elif res["t"] == "exited": res["code"] = canon(rv)
        res["argmut"] = canon([args, kwargs]); res["args_changed"] = json.dumps(res["argmut"]) != before_a
        after_g = {k: canon(v) for k, v in vars(mod).items()
                   if not k.startswith("__") and not callable(v) and not issubclass(type(v), types.ModuleType)}
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
