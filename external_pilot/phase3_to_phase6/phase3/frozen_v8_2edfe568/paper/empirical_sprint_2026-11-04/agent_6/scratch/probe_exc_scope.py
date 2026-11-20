"""Scratch (agent 6): (1) try/finally + generator-expression exception-event parity, Python Tracer vs repo JDI tracer;
(2) block-scoped local visibility in JDI snapshots. Structure only; no scoring; nothing written outside tempdirs/this dir."""
import sys, pathlib, shutil, types, textwrap
sys.dont_write_bytecode = True
REPO = pathlib.Path("/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG"); sys.path.insert(0, str(REPO))
from experiments.final import external_java as J
from sbg.extraction.dynamic.tracer import Tracer

JAVA = '''package java_programs;
public class FIN {
  static int cnt = 0;
  public static int fin(int x){
    try {
      return helper(x);
    } finally {
      cnt++;
    }
  }
  static int helper(int x){ return 10 / x; }
  public static int scope(int n){
    int total = 0;
    for (int i = 0; i < 2; i++) {
      int t = n * 2;
      total += t;
    }
    return total;
  }
}
'''
PY = textwrap.dedent('''
    cnt = 0
    def fin(x):
        global cnt
        try:
            return helper(x)
        finally:
            cnt += 1
    def helper(x):
        return 10 // x
    def gen(l):
        return any(v > 5 for v in l)
''')
def jtrace(entry, inputs):
    sig = J.entry_signature("FIN", JAVA.replace("public static int fin", "public static int fin"))
    # entry_signature matches method == class name lower() -> 'fin'; for 'scope' use a rename trick
    src = JAVA if entry == "fin" else JAVA.replace("class FIN", "class SCOPE").replace("scope(", "scope(")
    name = "FIN" if entry == "fin" else "SCOPE"
    sig = J.entry_signature(name, src)
    if sig is None: raise SystemExit("no sig " + entry)
    jin = J.inputs_to_java(sig, inputs)
    cls, err = J.compile_version(src, name, {"SbgHarness": J.harness_source(name, sig, jin)}, J.support_sources())
    assert cls, err
    runs, e, _ = J.run_traces(cls, len(jin), [repr(tuple(i)) for i in inputs], name); shutil.rmtree(cls.parent, ignore_errors=True)
    return runs[0]
def seq(t, keep=("call", "return", "exception")):
    return [(e.event_type, e.function_name) for e in t.events if e.event_type in keep]

jt = jtrace("fin", [[0], [2]])
m = types.ModuleType("m"); exec(compile(PY, "m.py", "exec"), m.__dict__)
pt = Tracer().trace(lambda a: m.fin(*a), [(0,), (2,)])
for i, x in enumerate((0, 2)):
    print(f"fin({x})  JAVA:", seq(jt[i]), "| exc:", jt[i].exception)
    print(f"fin({x})  PY  :", seq(pt[i]), "| exc:", pt[i].exception)
# generator expression exception events in Python
gt = Tracer().trace(lambda a: m.gen(*a), [([1, 2, 3],), ([9],)])
for i, t in enumerate(gt):
    print("PY any(genexpr) event types:", {k: sum(1 for e in t.events if e.event_type == k) for k in ("call", "exception", "return", "line")},
          "funcs:", sorted({e.function_name for e in t.events if e.event_type == 'call'}),
          "exception-event funcs:", [e.function_name for e in t.events if e.event_type == 'exception'])
# scope visibility
st = jtrace("scope", [[3]])[0]
print("JAVA scope() snapshots per line event:")
for e in st.events:
    if e.event_type == "line" and e.function_name == "scope":
        print("  line", e.lineno, sorted(e.local_vars_snapshot.items()))
