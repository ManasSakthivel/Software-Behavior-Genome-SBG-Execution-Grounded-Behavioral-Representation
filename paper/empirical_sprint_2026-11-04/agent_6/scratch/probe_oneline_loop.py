"""Scratch (agent 6): do one-line loops yield one line event per iteration in the Python tracer? (structure only; no scoring)"""
import sys, types, textwrap, pathlib, shutil
sys.dont_write_bytecode = True
REPO = pathlib.Path("/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG"); sys.path.insert(0, str(REPO))
from sbg.extraction.dynamic.tracer import Tracer
from experiments.final import external_java as J
PY = textwrap.dedent('''
    def one(n):
        total = 0
        for i in range(3): total += n
        return total
    def multi(n):
        total = 0
        for i in range(3):
            total += n
        return total
''')
m = types.ModuleType("m"); exec(compile(PY, "m.py", "exec"), m.__dict__)
for fn in ("one", "multi"):
    t = Tracer().trace(getattr(m, fn), [2])[0]
    print("PY  ", fn, "line events:", sum(1 for e in t.events if e.event_type == "line" and e.function_name == fn),
          "line seq:", [e.lineno for e in t.events if e.event_type == "line" and e.function_name == fn])
JAVA = '''package java_programs;
public class LOOPS {
  public static int one(int n){
    int total = 0;
    for (int i = 0; i < 3; i++) total += n;
    return total;
  }
  public static int multi(int n){
    int total = 0;
    for (int i = 0; i < 3; i++) {
      total += n;
    }
    return total;
  }
}
'''
for fn in ("one", "multi"):
    src = JAVA.replace("class LOOPS", "class " + fn.upper())
    # keep only the wanted method as entry; entry_signature picks method == class.lower()
    name = fn.upper()
    sig = J.entry_signature(name, src); jin = J.inputs_to_java(sig, [[2]])
    cls, err = J.compile_version(src, name, {"SbgHarness": J.harness_source(name, sig, jin)}, J.support_sources()); assert cls, err
    runs, e, _ = J.run_traces(cls, 1, ["(2,)"], name); shutil.rmtree(cls.parent, ignore_errors=True)
    t = runs[0][0]
    print("JAVA", fn, "line events:", sum(1 for ev in t.events if ev.event_type == "line" and ev.function_name == fn),
          "line seq:", [ev.lineno for ev in t.events if ev.event_type == "line" and ev.function_name == fn])
