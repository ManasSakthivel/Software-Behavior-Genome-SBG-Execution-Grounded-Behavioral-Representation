"""
Tests for the QuixBugs Java SBG-schema pipeline (experiments/final/external_java.py).

The decisive tests are the parity tests: the pre-registered criterion is that
Java counts as an SBG evaluation only if Java traces carry the same feature
schema as Python traces, so the same algorithm in both languages must yield
the same call / return / exception event structure, the same line events and
the same local-variable snapshots under the Python tracer and the JDI tracer.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import sys
import textwrap

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from experiments.final import external_java as J  # noqa: E402
from experiments.final import extraction as X      # noqa: E402

HAVE_JDK = shutil.which("javac") is not None and shutil.which("java") is not None
needs_jdk = pytest.mark.skipif(not HAVE_JDK, reason="JDK not available")

PY_GCD = textwrap.dedent('''
    def gcd(a, b):
        if b == 0:
            return a
        else:
            return gcd(b, a % b)
''')

PY_EXC = textwrap.dedent('''
    def outer(x):
        y = inner(x)
        return y + 1


    def inner(x):
        try:
            return helper(x)
        except ZeroDivisionError:
            return -1


    def helper(x):
        z = 10 // x
        return z


    def boom(x):
        return outer(x) + helper(x)
''')

JAVA_EXC = textwrap.dedent('''
    package java_programs;
    public class BOOM {
        public static int outer(int x) {
            int y = inner(x);
            return y + 1;
        }

        public static int inner(int x) {
            try {
                return helper(x);
            } catch (ArithmeticException e) {
                return -1;
            }
        }

        public static int helper(int x) {
            int z = 10 / x;
            return z;
        }

        public static int boom(int x) {
            return outer(x) + helper(x);
        }
    }
''')


def _pymodule(tmp_path, name, source):
    path = tmp_path / f"{name}.py"
    path.write_text(source)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _python_traces(fn, inputs):
    from sbg.extraction.dynamic.tracer import Tracer
    return Tracer().trace(lambda args: fn(*args), [tuple(i) for i in inputs])


def _java_traces(name, source, inputs):
    sig = J.entry_signature(name, source)
    java_inputs = J.inputs_to_java(sig, inputs)
    classes, err = J.compile_version(source, name, {"SbgHarness": J.harness_source(name, sig, java_inputs)},
                                     J.support_sources())
    assert classes is not None, err
    try:
        runs, error, _ = J.run_traces(classes, len(java_inputs), [repr(tuple(i)) for i in inputs], name)
    finally:
        shutil.rmtree(classes.parent, ignore_errors=True)
    assert error is None
    return runs[0]


def _structure(trace):
    return [(e.event_type, e.function_name) for e in trace.events
            if e.event_type in ("call", "return", "exception") and e.function_name != "<lambda>"]


def _lines(trace, fn):
    return sum(1 for e in trace.events if e.event_type == "line" and e.function_name == fn)


# ---------------------------------------------------------------------------
# Schema parity (the pre-registered criterion)
# ---------------------------------------------------------------------------

@needs_jdk
def test_gcd_trace_structure_matches_python(tmp_path):
    source = (J.CORPUS / "correct" / "GCD.java").read_text()
    inputs = [[17, 0], [13, 13], [37, 600], [624129, 2061517]]
    java = _java_traces("GCD", source, inputs)
    python = _python_traces(_pymodule(tmp_path, "gcd_ref", PY_GCD).gcd, inputs)
    for j, p in zip(java, python):
        assert _structure(j) == _structure(p)
        assert _lines(j, "gcd") == _lines(p, "gcd")
        j_call = [e.local_vars_snapshot for e in j.events if e.event_type == "call"]
        p_call = [e.local_vars_snapshot for e in p.events
                  if e.event_type == "call" and e.function_name == "gcd"]
        assert j_call == p_call


@needs_jdk
def test_exception_propagation_matches_python(tmp_path):
    inputs = [[0], [2]]
    java = _java_traces("BOOM", JAVA_EXC, inputs)
    python = _python_traces(_pymodule(tmp_path, "exc_ref", PY_EXC).boom, inputs)
    for j, p in zip(java, python):
        assert _structure(j) == _structure(p)
        assert (j.exception is None) == (p.exception is None)


@needs_jdk
def test_java_traces_featurise_through_python_pipeline():
    source = (J.CORPUS / "correct" / "BITCOUNT.java").read_text()
    sig = J.entry_signature("BITCOUNT", source)
    inputs = J.canonical_inputs(sig)
    record, _ = J.trace_version("BITCOUNT", source, sig, J.inputs_to_java(sig, inputs),
                                [repr(tuple(i)) for i in inputs], "correct")
    assert record.ok
    assert record.genome_v3 is not None and record.temporal is not None and record.state is not None
    assert record.stats["n_traces"] == X.N_RUNS * len(inputs)
    scores = X.score_pair(record, record)
    assert scores["sbg_v5"] == 0.0 and scores["v5_full"] == 1.0


# ---------------------------------------------------------------------------
# Corpus integrity and output-freedom
# ---------------------------------------------------------------------------

def test_corpus_matches_frozen_manifest():
    manifest = json.loads((J.CORPUS / "MANIFEST.json").read_text())
    assert manifest["commit"] == J.QUIXBUGS_COMMIT
    J._verify_manifest(manifest)
    assert len(manifest["programs"]) == 40


def test_declared_inputs_carry_no_expected_outputs():
    declared = json.loads((J.CORPUS / "declared_inputs.json").read_text())
    for name, cases in declared.items():
        source = (J.CORPUS / "correct" / f"{name}.java").read_text()
        sig = J.entry_signature(name, source)
        assert len(cases) <= J.N_INPUTS
        for args in cases:
            # every stored case is an argument list whose arity is the entry's
            assert isinstance(args, list)
            assert len(args) == len(sig["params"]), name


def test_harness_never_reads_the_entry_result():
    source = (J.CORPUS / "correct" / "BUCKETSORT.java").read_text()
    sig = J.entry_signature("BUCKETSORT", source)
    text = J.harness_source("BUCKETSORT", sig, J.inputs_to_java(sig, J.canonical_inputs(sig)))
    body = text[text.index("static void run"):]
    assert "System.out" not in text and "=" not in body.split("switch")[1].split("}")[0]


# ---------------------------------------------------------------------------
# Signature and input rules
# ---------------------------------------------------------------------------

def test_entry_is_the_method_named_after_the_class():
    src = (J.CORPUS / "correct" / "MERGESORT.java").read_text()
    assert J.entry_signature("MERGESORT", src)["method"] == "mergesort"
    src = (J.CORPUS / "correct" / "FIND_IN_SORTED.java").read_text()
    assert J.entry_signature("FIND_IN_SORTED", src)["method"] == "find_in_sorted"


def test_type_families_mirror_the_protocol():
    assert J.java_family("int") == "int"
    assert J.java_family("ArrayList<Integer>") == "list"
    assert J.java_family("int[]") == "list"
    assert J.java_family("Object") == "list"
    assert J.java_family("Node") is None
    assert J.java_family("int[][]") is None
    assert J.java_family("Map<List<String>,Integer>") is None


def test_canonical_inputs_are_the_protocol_batteries():
    from experiments.final import protocol as P
    src = (J.CORPUS / "correct" / "BUCKETSORT.java").read_text()
    inputs = J.canonical_inputs(J.entry_signature("BUCKETSORT", src))
    assert len(inputs) == P.BATTERY_SIZE
    assert [i[0] for i in inputs] == P.LIST_BATTERY
    assert [i[1] for i in inputs] == P.INT_BATTERY


def test_generic_parameter_lists_split_at_top_level():
    assert J.split_top_level("Map<List<String>,Integer> w, int k") == ["Map<List<String>,Integer> w", "int k"]


# ---------------------------------------------------------------------------
# Negatives are proven semantics-preserving
# ---------------------------------------------------------------------------

@needs_jdk
def test_negatives_compile_to_identical_bytecode():
    name = "LEVENSHTEIN"
    src = (J.CORPUS / "correct" / f"{name}.java").read_text()
    sig = J.entry_signature(name, src)
    negatives = [n for n in J.make_negatives(name, src, sig) if n.get("source")]
    assert negatives
    base, _ = J.compile_version(src, name, {}, J.support_sources())
    try:
        want = J.bytecode_signature(base)
    finally:
        shutil.rmtree(base.parent, ignore_errors=True)
    for neg in negatives:
        assert neg["source"] != src
        classes, err = J.compile_version(neg["source"], name, {}, J.support_sources())
        assert classes is not None, err
        try:
            assert J.bytecode_signature(classes) == want
        finally:
            shutil.rmtree(classes.parent, ignore_errors=True)


def test_java_token_multiset_skips_comments_and_strings():
    a = J.java_token_multiset('int x = 1; // note\n/* block */ String s = "a b";')
    assert ("NAME", "note") not in a and ("NAME", "block") not in a
    assert ("OP", "=") in a and ("NAME", "String") in a
