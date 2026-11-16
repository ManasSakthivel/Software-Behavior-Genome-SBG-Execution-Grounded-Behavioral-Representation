"""Helper for EXP-A3-009 (run as subprocess): python _exec_probe.py <abs_path> <entry> <json list of input reprs>
Executes entry on deep-copied inputs (literal_eval of the recorded input repr; tuple => *args) and prints JSON
[[status, ret_repr<=300, arg_repr_after<=300, stdout<=200] ...] .  Pure stdlib; 5 s alarm per input; no repo code imported."""
import ast, contextlib, copy, importlib.util, io, json, re, signal, sys
path, entry, inputs = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
class TO(BaseException): pass
def h(*a): raise TO()
signal.signal(signal.SIGALRM, h)
out = []
try:
    spec = importlib.util.spec_from_file_location("_m", path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    f = getattr(m, entry)
except BaseException as e:
    print(json.dumps({"load_error": type(e).__name__})); sys.exit(0)
for r in inputs:
    try:
        i = ast.literal_eval(r)
    except Exception:
        out.append(["unparseable_input", r[:80], "", ""]); continue
    a = copy.deepcopy(i); buf = io.StringIO()
    signal.alarm(5)
    try:
        with contextlib.redirect_stdout(buf):
            res = f(*a) if isinstance(a, tuple) else f(a)
        out.append(["ok", re.sub(r"0x[0-9a-f]+", "0x?", repr(res))[:300], repr(a)[:300], buf.getvalue()[:200]])
    except TO:
        out.append(["timeout", "", "", ""])
    except BaseException as e:
        out.append(["exc", type(e).__name__, repr(a)[:300], buf.getvalue()[:200]])
    finally:
        signal.alarm(0)
print(json.dumps(out))
