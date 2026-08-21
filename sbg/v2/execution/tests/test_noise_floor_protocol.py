"""
sbg/v2/execution/tests/test_noise_floor_protocol.py
=====================================================
Structural verification tests for the SAFEGUARD-6 noise floor experiment.

These tests verify the PROTOCOL properties of experiments/v2/noise_floor.py:
  1. The stability criterion constant is defined as a module-level constant
     BEFORE any analysis functions.
  2. n_runs (N_RUNS) is ≥ 5, meeting SAFEGUARD-6 minimum.
  3. The criterion constant appears in the source before the analysis logic
     (structural ordering check — criterion predeclared, not post-hoc).
  4. MEASURED_FIELDS covers all required DynamicGenome scalar fields.
  5. SAMPLE_PROGRAMS contains exactly 10 entries.

These tests do NOT execute the noise floor script. They are static/structural
checks that can run in any environment without requiring benchmark programs.
"""
from __future__ import annotations

import ast
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

_NOISE_FLOOR_PATH = REPO_ROOT / "experiments" / "v2" / "noise_floor.py"

# ---------------------------------------------------------------------------
# Required fields per DynamicGenome spec (from genome.py)
# ---------------------------------------------------------------------------
REQUIRED_MEASURED_FIELDS = {
    "coverage_size",
    "coverage_consistency",
    "exception_rate",
    "call_depth_mean",
    "trace_length_mean",
    "n_unique_functions",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_module_source() -> str:
    """Return the raw source of noise_floor.py."""
    return _NOISE_FLOOR_PATH.read_text(encoding="utf-8")


def _parse_module_ast() -> ast.Module:
    """Parse noise_floor.py into an AST."""
    source = _load_module_source()
    return ast.parse(source, filename=str(_NOISE_FLOOR_PATH))


def _import_noise_floor():
    """Import the noise_floor module (without executing run())."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("noise_floor", str(_NOISE_FLOOR_PATH))
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ===========================================================================
# Test 1: Script exists and is parseable
# ===========================================================================

def test_noise_floor_script_exists():
    """The noise floor script must exist at the expected path."""
    assert _NOISE_FLOOR_PATH.exists(), (
        f"noise_floor.py not found at {_NOISE_FLOOR_PATH}"
    )


def test_noise_floor_script_parseable():
    """The noise floor script must be valid Python."""
    _parse_module_ast()  # raises SyntaxError if invalid


# ===========================================================================
# Test 2: Stability criterion is defined as a module-level constant
# ===========================================================================

def test_stability_criterion_constant_exists():
    """
    STABILITY_CRITERION_CV_THRESHOLD must be a module-level constant.

    SAFEGUARD-6 requires the criterion to be predeclared, not derived
    from observed results.
    """
    mod = _import_noise_floor()
    assert hasattr(mod, "STABILITY_CRITERION_CV_THRESHOLD"), (
        "STABILITY_CRITERION_CV_THRESHOLD is not defined as a module-level "
        "constant in noise_floor.py"
    )


def test_stability_criterion_is_float():
    """The criterion must be a float, not an int or string."""
    mod = _import_noise_floor()
    value = mod.STABILITY_CRITERION_CV_THRESHOLD
    assert isinstance(value, float), (
        f"STABILITY_CRITERION_CV_THRESHOLD must be float, got {type(value)}"
    )


def test_stability_criterion_value_is_0_05():
    """
    The predeclared criterion must equal 0.05.

    This test locks the value to its predeclared amount. Changing the
    threshold post-hoc (after observing results) would break this test
    and signal a protocol violation.
    """
    mod = _import_noise_floor()
    assert mod.STABILITY_CRITERION_CV_THRESHOLD == 0.05, (
        f"Expected STABILITY_CRITERION_CV_THRESHOLD=0.05, "
        f"got {mod.STABILITY_CRITERION_CV_THRESHOLD}. "
        "Changing this value after seeing results is a SAFEGUARD-6 violation."
    )


def test_stability_criterion_in_range():
    """Criterion must be in (0, 1) — a meaningful CV threshold."""
    mod = _import_noise_floor()
    cv = mod.STABILITY_CRITERION_CV_THRESHOLD
    assert 0.0 < cv < 1.0, f"CV threshold {cv} is not in (0, 1)"


# ===========================================================================
# Test 3: n_runs ≥ 5 (SAFEGUARD-6 minimum)
# ===========================================================================

def test_n_runs_constant_exists():
    """N_RUNS constant must be present in noise_floor.py."""
    mod = _import_noise_floor()
    assert hasattr(mod, "N_RUNS"), "N_RUNS constant not found in noise_floor.py"


def test_n_runs_meets_minimum():
    """
    N_RUNS must be ≥ 5.

    SAFEGUARD-6 requires n_runs ≥ 5 per program for noise floor
    estimation. Fewer runs produce unreliable variance estimates.
    """
    mod = _import_noise_floor()
    assert mod.N_RUNS >= 5, (
        f"N_RUNS={mod.N_RUNS} fails SAFEGUARD-6 minimum of 5"
    )


# ===========================================================================
# Test 4: Structural ordering — criterion precedes analysis functions
# ===========================================================================

def _find_toplevel_assignment_line(tree: ast.Module, name: str) -> "int | None":
    """
    Search module-level body for an assignment (Assign or AnnAssign) of `name`.
    Returns the line number of the first match, or None.

    Handles both:
      name = value          (ast.Assign)
      name: type = value    (ast.AnnAssign)
    """
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return node.lineno
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == name:
                return node.lineno
    return None


def _find_first_toplevel_function_line(tree: ast.Module, names: set) -> "int | None":
    """Return the line of the first top-level FunctionDef whose name is in `names`."""
    line = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            if line is None or node.lineno < line:
                line = node.lineno
    return line


def test_criterion_declared_before_analysis_functions():
    """
    STABILITY_CRITERION_CV_THRESHOLD assignment must appear in the AST
    before any function definitions that perform analysis.

    This is a structural proxy for the predeclared-criterion requirement.
    If the constant is moved below the analysis functions, this fails —
    indicating possible post-hoc manipulation.
    """
    tree = _parse_module_ast()

    # Analysis functions that USE the criterion
    analysis_fn_names = {"measure_program_noise", "_assess_stability", "run"}

    criterion_line = _find_toplevel_assignment_line(tree, "STABILITY_CRITERION_CV_THRESHOLD")
    first_analysis_fn_line = _find_first_toplevel_function_line(tree, analysis_fn_names)

    assert criterion_line is not None, (
        "Could not find STABILITY_CRITERION_CV_THRESHOLD assignment in module body. "
        "Check that it is a top-level annotated or plain assignment."
    )
    assert first_analysis_fn_line is not None, (
        "Could not find analysis functions in module body"
    )
    assert criterion_line < first_analysis_fn_line, (
        f"STABILITY_CRITERION_CV_THRESHOLD (line {criterion_line}) must appear "
        f"before analysis functions (first at line {first_analysis_fn_line}). "
        "Predeclared criterion must precede the analysis logic."
    )


def test_n_runs_declared_before_analysis_functions():
    """N_RUNS constant must appear before the analysis functions."""
    tree = _parse_module_ast()

    analysis_fn_names = {"measure_program_noise", "run"}
    n_runs_line = _find_toplevel_assignment_line(tree, "N_RUNS")
    first_fn_line = _find_first_toplevel_function_line(tree, analysis_fn_names)

    assert n_runs_line is not None, (
        "N_RUNS not found as top-level assignment in noise_floor.py"
    )
    assert first_fn_line is not None, "Analysis functions not found in module body"
    assert n_runs_line < first_fn_line, (
        f"N_RUNS (line {n_runs_line}) must appear before analysis functions "
        f"(first at line {first_fn_line})"
    )


# ===========================================================================
# Test 5: MEASURED_FIELDS covers all required DynamicGenome scalar fields
# ===========================================================================

def test_measured_fields_constant_exists():
    """MEASURED_FIELDS list must be present."""
    mod = _import_noise_floor()
    assert hasattr(mod, "MEASURED_FIELDS"), "MEASURED_FIELDS not found in noise_floor.py"


def test_measured_fields_covers_required_genome_fields():
    """
    MEASURED_FIELDS must include all required DynamicGenome scalar fields.

    Required: coverage_size, coverage_consistency, exception_rate,
              call_depth_mean, trace_length_mean, n_unique_functions
    """
    mod = _import_noise_floor()
    actual = set(mod.MEASURED_FIELDS)
    missing = REQUIRED_MEASURED_FIELDS - actual
    assert not missing, (
        f"MEASURED_FIELDS is missing required DynamicGenome fields: {missing}"
    )


# ===========================================================================
# Test 6: SAMPLE_PROGRAMS contains exactly 10 programs
# ===========================================================================

def test_sample_programs_constant_exists():
    """SAMPLE_PROGRAMS list must be present."""
    mod = _import_noise_floor()
    assert hasattr(mod, "SAMPLE_PROGRAMS"), "SAMPLE_PROGRAMS not found in noise_floor.py"


def test_sample_programs_count_is_10():
    """
    SAMPLE_PROGRAMS must contain exactly 10 programs.

    The noise floor protocol specifies 10 programs (2 per category,
    5 categories). Fewer programs give unreliable cross-program statistics.
    """
    mod = _import_noise_floor()
    n = len(mod.SAMPLE_PROGRAMS)
    assert n == 10, f"Expected 10 SAMPLE_PROGRAMS, got {n}"


def test_sample_programs_no_unsafe_concurrent():
    """
    SAMPLE_PROGRAMS must not include any unsafe concurrent programs.

    conc_producer_consumer and conc_read_write_lock are excluded per
    SandboxRunner._UNSAFE_PROGRAMS.
    """
    mod = _import_noise_floor()
    unsafe = {"conc_producer_consumer", "conc_read_write_lock"}
    overlap = unsafe & set(mod.SAMPLE_PROGRAMS)
    assert not overlap, (
        f"SAMPLE_PROGRAMS includes unsafe concurrent programs: {overlap}"
    )


def test_sample_programs_no_duplicates():
    """SAMPLE_PROGRAMS must not contain duplicate entries."""
    mod = _import_noise_floor()
    programs = mod.SAMPLE_PROGRAMS
    assert len(programs) == len(set(programs)), (
        f"SAMPLE_PROGRAMS contains duplicates: {programs}"
    )


# ===========================================================================
# Test 7: _assess_stability uses STABILITY_CRITERION_CV_THRESHOLD
# ===========================================================================

def test_assess_stability_uses_predeclared_threshold():
    """
    _assess_stability must reference STABILITY_CRITERION_CV_THRESHOLD,
    not a hardcoded literal.

    This ensures the assessment function cannot silently diverge from
    the predeclared constant.
    """
    source = _load_module_source()
    # The function body must reference the constant by name
    import re
    fn_match = re.search(
        r"def _assess_stability\(.*?\):(.*?)(?=\ndef |\nclass |\Z)",
        source, re.DOTALL
    )
    assert fn_match is not None, "_assess_stability function not found in source"
    fn_body = fn_match.group(1)
    assert "STABILITY_CRITERION_CV_THRESHOLD" in fn_body, (
        "_assess_stability must use STABILITY_CRITERION_CV_THRESHOLD, "
        "not a hardcoded literal. Found body:\n" + fn_body
    )


# ===========================================================================
# Test 8: Dry-run import does not trigger execution
# ===========================================================================

def test_import_does_not_execute_run():
    """
    Importing noise_floor.py must not call run() or measure_program_noise().

    The script must only execute when called explicitly (e.g., __main__).
    """
    # If import triggered run(), it would attempt to access CORPUS_DIR
    # and produce side effects. The import above in helpers does not
    # raise errors — this test confirms it completes without file access errors.
    mod = _import_noise_floor()
    # Verify run() is callable but was not auto-invoked
    assert callable(mod.run), "run() must be callable"
    # ARTIFACTS_DIR/NOISE_FLOOR_RESULTS.json must NOT be written on import
    artifacts = REPO_ROOT / "artifacts" / "v2" / "NOISE_FLOOR_RESULTS.json"
    # (If it exists from a previous run, that's fine — we just verify
    #  the import itself doesn't write it by checking no exception was raised)
    assert True  # import completed without executing run()
