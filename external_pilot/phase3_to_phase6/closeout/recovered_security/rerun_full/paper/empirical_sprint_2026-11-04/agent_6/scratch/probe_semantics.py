"""Scratch (agent 6): what does the existing JDI tracer emit for overloads / inner class / lambda / block-scoped locals?
Compiles a synthetic class in a tempdir (repo helper does that), traces 1 input. No scoring. Nothing written outside this dir/tempdir."""
import sys, pathlib, shutil, time
sys.dont_write_bytecode = True
REPO = pathlib.Path("/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG"); sys.path.insert(0, str(REPO))
from experiments.final import external_java as J
SRC = '''package java_programs;
import java.util.*;
public class PROBE {
  static int f(int a){ return a+1; }
  static int f(int a,int b){ return a+b; }
  static class Inner { int f(int a){ return a*2; } }
  public static int probe(int n){
    int total = 0;
    for (int i=0;i<2;i++){ int t = n*2; total += t; }
    total += f(1) + f(1,2) + new Inner().f(3);
    java.util.function.IntUnaryOperator op = x -> x+1;
    total += op.applyAsInt(1);
    Integer boxed = null;
    return total;
  }
}
'''
sig = J.entry_signature("PROBE", SRC)
jin = J.inputs_to_java(sig, [[3]])
cls, err = J.compile_version(SRC, "PROBE", {"SbgHarness": J.harness_source("PROBE", sig, jin)}, J.support_sources())
assert cls, err
runs, e, _ = J.run_traces(cls, 1, ["(3,)"], "PROBE"); shutil.rmtree(cls.parent, ignore_errors=True)
t = runs[0][0]
print("call events (function_name):", [ev.function_name for ev in t.events if ev.event_type == "call"])
print("line-event snapshots of probe() (line -> keys):")
for ev in t.events:
    if ev.event_type == "line" and ev.function_name == "probe":
        print("  ", ev.lineno, sorted(ev.local_vars_snapshot.items()))
