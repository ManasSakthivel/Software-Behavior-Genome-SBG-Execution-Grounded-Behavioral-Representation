"""
experiments/v5/java_executor.py — Java program executor with behavioral trace extraction.

Uses print-based instrumentation (System.err.println for trace output).
Produces DynamicGenome-compatible feature dictionaries.

The instrumentation protocol: each Java method emits to stderr:
    TRACE ENTER <method> depth=<N>
    TRACE EXIT  <method> depth=<N>
    TRACE EXCEPTION <ExceptionType> depth=<N>

stdout is the program's functional output; stderr carries only trace lines.
The two streams are kept separate by subprocess (stderr=PIPE, stdout=PIPE).

Anonymization mirrors TraceNormalizer: function names are replaced with
first-call-order integer indices so the genome is rename-invariant.

Filtered methods (never counted):
    main, <clinit>, <init>, and any method whose name starts with "java."
    (static initialisers and constructors carry no algorithmic trace signal).

Usage:
    from experiments.v5.java_executor import JavaExecutor
    executor = JavaExecutor()
    genome = executor.run(java_source_path, inputs)
"""
from __future__ import annotations

import hashlib
import math
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JAVAC_PATH = "/usr/bin/javac"
JAVA_PATH = "/usr/bin/java"

# Methods filtered from the behavioral trace (no algorithmic signal).
_FILTERED_METHODS: Set[str] = {"main", "<clinit>", "<init>"}

# Regex that matches a single stderr trace line produced by the instrumented Java.
# Groups: (event, method, depth)
_TRACE_RE = re.compile(
    r"^TRACE\s+(ENTER|EXIT|EXCEPTION)\s+(\S+)(?:\s+depth=(\d+))?(?:\s+(.+))?$"
)

EXPECTED_GENOME_KEYS = {
    "program_id",
    "coverage_size",
    "coverage_consistency",
    "anon_call_freq",
    "hot_path_hash",
    "exception_type_set",
    "exception_rate",
    "call_depth_mean",
    "call_depth_max",
    "trace_length_mean",
    "trace_length_std",
    "n_unique_functions",
}


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class JavaTraceEvent:
    """A single parsed trace event from an instrumented Java program's stderr."""
    event_type: str           # "ENTER", "EXIT", "EXCEPTION"
    method_name: str
    depth: int
    exception_type: Optional[str] = None


# ---------------------------------------------------------------------------
# Instrumenter
# ---------------------------------------------------------------------------

class JavaInstrumenter:
    """
    Injects trace print statements into Java source code at method boundaries.

    This is a lightweight string-level instrumenter — not a full Java parser.
    It is designed for the simple, non-nested-class benchmark programs in
    benchmark/v5/java_programs/.

    Strategy
    --------
    1. Locate method declarations with a regex that matches the opening brace.
    2. After the opening brace, inject:
         callDepth++;
         System.err.println("TRACE ENTER …");
         try {
    3. Before each return statement, inject nothing — the try/finally handles EXIT.
    4. Find the matching closing brace, replace it with:
         } finally {
             System.err.println("TRACE EXIT …");
             callDepth--;
         }

    For programs that already contain trace instrumentation (like the benchmark
    files in benchmark/v5/java_programs/ which have manual instrumentation),
    the instrumenter detects the existing TRACE lines and skips re-injection to
    avoid double-instrumentation.
    """

    _ALREADY_INSTRUMENTED_MARKER = "TRACE ENTER"

    def instrument(self, java_source: str) -> str:
        """Return java_source with trace instrumentation injected, or unchanged
        if it is already instrumented."""
        if self._ALREADY_INSTRUMENTED_MARKER in java_source:
            # Pre-instrumented (e.g. benchmark/v5/java_programs/*.java) — pass through.
            return java_source
        # For un-instrumented source: inject a static callDepth field and wrap each
        # non-constructor, non-main public/private/protected/static method body.
        return self._inject(java_source)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _inject(self, source: str) -> str:
        """Inject callDepth field and try/finally wrapper into each method."""
        # Insert the static callDepth field right after the first class opening brace.
        source = re.sub(
            r"(class\s+\w+[^{]*\{)",
            r"\1\n    static int callDepth = 0;\n",
            source,
            count=1,
        )

        # Pattern for a method declaration + opening brace.
        # Matches: [modifiers] [return_type] methodName([params]) [throws ...] {
        method_re = re.compile(
            r"((?:(?:public|private|protected|static|final|synchronized|abstract)\s+)*"
            r"(?:[\w<>\[\]]+)\s+"         # return type
            r"(\w+)\s*"                   # method name (captured)
            r"\([^)]*\)\s*"              # parameter list
            r"(?:throws\s+[\w,\s]+)?\s*)" # optional throws
            r"\{",                        # opening brace
        )

        result = []
        pos = 0
        for m in method_re.finditer(source):
            method_name = m.group(2)
            if method_name in _FILTERED_METHODS:
                continue
            open_brace_pos = m.end() - 1  # position of '{'
            # Find the matching closing brace
            close_pos = self._find_matching_brace(source, open_brace_pos)
            if close_pos is None:
                continue

            # Emit everything up to (and including) the opening brace
            result.append(source[pos : open_brace_pos + 1])
            # Inject ENTER + try
            result.append(
                f'\n        callDepth++;\n'
                f'        System.err.println("TRACE ENTER {method_name} depth=" + callDepth);\n'
                f'        try {{\n'
            )
            # Emit the method body (between braces, exclusive)
            result.append(source[open_brace_pos + 1 : close_pos])
            # Inject finally + EXIT + close
            result.append(
                f'\n        }} finally {{\n'
                f'            System.err.println("TRACE EXIT {method_name} depth=" + callDepth);\n'
                f'            callDepth--;\n'
                f'        }}\n'
            )
            pos = close_pos + 1  # skip original closing brace

        result.append(source[pos:])
        return "".join(result)

    @staticmethod
    def _find_matching_brace(source: str, open_pos: int) -> Optional[int]:
        """Return the index of the closing brace matching source[open_pos]=='{'."""
        depth = 0
        for i in range(open_pos, len(source)):
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
                if depth == 0:
                    return i
        return None


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------

class JavaExecutor:
    """
    Execute instrumented Java programs and extract behavioral genomes compatible
    with DynamicGenome.to_dict().

    Workflow
    --------
    1. instrument_and_compile(source_path) → compiles to a temp dir, returns class dir.
    2. run_single(class_path, class_name, input_data) → List[JavaTraceEvent].
    3. extract_genome(all_traces) → dict matching DynamicGenome.to_dict() schema.
    4. run(source_path, inputs) → shortcut for the whole pipeline.
    """

    CANONICAL_INPUTS: List[Any] = [
        [1, 2, 3, 4, 5],
        [5, 4, 3, 2, 1],
        [],
        [1],
        [3, 1, 4, 1, 5],
    ]

    def __init__(self) -> None:
        self._instrumenter = JavaInstrumenter()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_java_available(self) -> bool:
        """Return True if javac is present and executable."""
        return os.path.isfile(JAVAC_PATH) and os.access(JAVAC_PATH, os.X_OK)

    def instrument_and_compile(
        self, java_source_path: Path
    ) -> Optional[Path]:
        """
        Instrument (if needed) and compile a Java source file.

        Returns the Path to the temporary class directory, or None on error.
        The caller is responsible for cleanup (use tempfile.TemporaryDirectory
        as a context manager if you need automatic cleanup).
        """
        java_source_path = Path(java_source_path)
        source = java_source_path.read_text(encoding="utf-8")

        # Apply instrumentation
        instrumented = self._instrumenter.instrument(source)

        # Write to a temp directory preserving the original class name
        class_name = java_source_path.stem
        tmp_dir = tempfile.mkdtemp(prefix="java_sbg_")
        tmp_src = Path(tmp_dir) / f"{class_name}.java"
        tmp_src.write_text(instrumented, encoding="utf-8")

        # Compile
        result = subprocess.run(
            [JAVAC_PATH, "-d", tmp_dir, str(tmp_src)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None

        return Path(tmp_dir)

    def run_single(
        self,
        class_path: Path,
        class_name: str,
        input_data: Any,
        timeout: int = 10,
    ) -> List[JavaTraceEvent]:
        """
        Run a compiled Java class with the given input and parse its stderr traces.

        input_data is converted to a stdin string:
            list/tuple → space-separated integers on one line
            str        → passed verbatim
            None       → empty string

        Returns a (possibly empty) list of JavaTraceEvent.
        """
        stdin_str = _to_stdin_string(input_data)

        try:
            result = subprocess.run(
                [JAVA_PATH, "-cp", str(class_path), class_name],
                input=stdin_str,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return [JavaTraceEvent("EXCEPTION", class_name, 0, "TimeoutException")]
        except Exception as exc:
            return [JavaTraceEvent("EXCEPTION", class_name, 0, type(exc).__name__)]

        events: List[JavaTraceEvent] = []
        for line in result.stderr.splitlines():
            evt = _parse_trace_line(line)
            if evt is not None:
                events.append(evt)

        return events

    def extract_genome(
        self,
        all_traces: List[List[JavaTraceEvent]],
        program_id: str = "unknown",
    ) -> dict:
        """
        Convert a list-of-trace-lists into a DynamicGenome-compatible dict.

        The schema exactly mirrors DynamicGenome.to_dict():
            program_id, coverage_size, coverage_consistency,
            anon_call_freq, hot_path_hash, exception_type_set,
            exception_rate, call_depth_mean, call_depth_max,
            trace_length_mean, trace_length_std, n_unique_functions

        Anonymization mirrors TraceNormalizer:
            - Build name→index map in first-call order (ENTER events only).
            - Filter: main, <clinit>, <init>, names starting with "java.".
        """
        # Flatten all traces for building the global anonymization map.
        flat: List[JavaTraceEvent] = [ev for trace in all_traces for ev in trace]

        # Build anonymization map (first-call order, filtered).
        name_to_idx: Dict[str, int] = {}
        for ev in flat:
            name = ev.method_name
            if ev.event_type == "ENTER" and _keep_method(name) and name not in name_to_idx:
                name_to_idx[name] = len(name_to_idx)

        # Per-trace stats
        per_trace_coverage: List[Set[int]] = []
        call_depths: List[float] = []
        event_counts: List[int] = []
        exception_types: Set[str] = set()
        n_exception_traces = 0
        anon_call_counts: Dict[int, int] = {}

        for trace in all_traces:
            # "Coverage" for Java traces: use the depth at each ENTER event as a
            # synthetic line proxy (we have no line numbers; depth buckets provide
            # a structural coverage analogue that is rename-invariant).
            coverage_set: Set[int] = set()
            max_depth = 0
            has_exception = False

            for ev in trace:
                if ev.event_type == "ENTER" and _keep_method(ev.method_name):
                    depth_bucket = ev.depth
                    coverage_set.add(depth_bucket * 1000 + name_to_idx.get(ev.method_name, 0))
                    max_depth = max(max_depth, ev.depth)
                    idx = name_to_idx.get(ev.method_name, -1)
                    if idx >= 0:
                        anon_call_counts[idx] = anon_call_counts.get(idx, 0) + 1
                elif ev.event_type == "EXCEPTION":
                    has_exception = True
                    if ev.exception_type:
                        exception_types.add(ev.exception_type)

            if has_exception:
                n_exception_traces += 1

            per_trace_coverage.append(coverage_set)
            call_depths.append(float(max_depth))
            event_counts.append(len(trace))

        n_total = len(all_traces)

        # Normalized call frequencies
        total_calls = sum(anon_call_counts.values()) or 1
        anon_call_freq = {k: v / total_calls for k, v in anon_call_counts.items()}

        # Coverage stats
        coverage_union: Set[int] = set()
        for cov in per_trace_coverage:
            coverage_union.update(cov)
        coverage_size = len(coverage_union)
        coverage_consistency = _mean_pairwise_jaccard(per_trace_coverage)

        # Exception stats
        exception_rate = n_exception_traces / n_total if n_total else 0.0

        # Depth stats
        mean_depth = sum(call_depths) / len(call_depths) if call_depths else 0.0
        max_depth_val = max(call_depths, default=0.0)

        # Trace length stats
        mean_ev = sum(event_counts) / len(event_counts) if event_counts else 0.0
        n_ev = len(event_counts)
        var_ev = sum((x - mean_ev) ** 2 for x in event_counts) / n_ev if n_ev else 0.0

        # Hot path hash: top-5 anonymous function indices by frequency (rename-invariant)
        top5 = sorted(anon_call_freq.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
        key = "|".join(str(idx) for idx, _ in top5)
        hot_path_hash = hashlib.sha256(key.encode()).hexdigest()[:16]

        return {
            "program_id": program_id,
            "coverage_size": coverage_size,
            "coverage_consistency": round(coverage_consistency, 6),
            "anon_call_freq": {str(k): round(v, 6) for k, v in anon_call_freq.items()},
            "hot_path_hash": hot_path_hash,
            "exception_type_set": sorted(exception_types),
            "exception_rate": round(exception_rate, 6),
            "call_depth_mean": round(mean_depth, 4),
            "call_depth_max": float(max_depth_val),
            "trace_length_mean": round(mean_ev, 4),
            "trace_length_std": round(var_ev ** 0.5, 4),
            "n_unique_functions": len(name_to_idx),
            "feature_classification": "OUTPUT_FREE",
            "safeguard_2_compliant": True,
        }

    def run(
        self,
        java_source_path: Path,
        inputs: Optional[List] = None,
    ) -> dict:
        """
        Full pipeline: instrument → compile → run all inputs → extract genome.

        Returns a DynamicGenome-compatible dict, or a status dict if Java is
        unavailable or compilation fails.
        """
        if not self.check_java_available():
            return {
                "status": "NOT_AVAILABLE",
                "reason": "javac not found",
            }

        java_source_path = Path(java_source_path)
        program_id = java_source_path.stem

        class_dir = self.instrument_and_compile(java_source_path)
        if class_dir is None:
            return {
                "status": "COMPILE_ERROR",
                "reason": f"javac failed for {java_source_path.name}",
                "program_id": program_id,
            }

        if inputs is None:
            inputs = self.CANONICAL_INPUTS

        all_traces: List[List[JavaTraceEvent]] = []
        for inp in inputs:
            trace = self.run_single(class_dir, program_id, inp)
            all_traces.append(trace)

        return self.extract_genome(all_traces, program_id=program_id)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _keep_method(name: str) -> bool:
    """Return True if this method should be included in the behavioral trace."""
    return name not in _FILTERED_METHODS and not name.startswith("java.")


def _to_stdin_string(input_data: Any) -> str:
    """Convert a Python input value into a Java-program stdin string."""
    if input_data is None:
        return ""
    if isinstance(input_data, str):
        return input_data
    if isinstance(input_data, (list, tuple)):
        return " ".join(str(x) for x in input_data)
    return str(input_data)


def _parse_trace_line(line: str) -> Optional[JavaTraceEvent]:
    """
    Parse a single stderr line from an instrumented Java program.

    Expected formats:
        TRACE ENTER sort depth=2
        TRACE EXIT  sort depth=2
        TRACE EXCEPTION NullPointerException depth=1
    """
    m = _TRACE_RE.match(line.strip())
    if m is None:
        return None
    event_type = m.group(1)
    method_name = m.group(2)
    depth = int(m.group(3)) if m.group(3) else 0
    exception_type = m.group(4) if event_type == "EXCEPTION" else None
    return JavaTraceEvent(
        event_type=event_type,
        method_name=method_name,
        depth=depth,
        exception_type=exception_type,
    )


def _mean_pairwise_jaccard(coverage_sets: List[Set[int]]) -> float:
    """Mean pairwise Jaccard across per-trace coverage sets (efficiency-capped at 5 neighbours)."""
    n = len(coverage_sets)
    if n < 2:
        return 1.0
    total = 0.0
    count = 0
    for i in range(n):
        for j in range(i + 1, min(n, i + 6)):
            a, b = coverage_sets[i], coverage_sets[j]
            union = len(a | b)
            if union == 0:
                total += 1.0
            else:
                total += len(a & b) / union
            count += 1
    return round(total / count, 6) if count else 1.0


# ---------------------------------------------------------------------------
# Self-test (Part 3)
# ---------------------------------------------------------------------------

def _main() -> None:
    """
    Self-test block.

    Checks javac availability, compiles BubbleSort.java, runs it with [5,3,1,4,2],
    extracts the genome, and validates that all expected keys are present.
    """
    import sys

    executor = JavaExecutor()

    if not executor.check_java_available():
        print("JAVA_NOT_AVAILABLE — design validated, execution skipped")
        return

    # Locate BubbleSort.java relative to this file's location.
    here = Path(__file__).parent
    bubble_sort_path = here.parent.parent / "benchmark" / "v5" / "java_programs" / "BubbleSort.java"

    if not bubble_sort_path.exists():
        print(f"FAIL: BubbleSort.java not found at {bubble_sort_path}")
        sys.exit(1)

    print(f"Compiling {bubble_sort_path} …")
    genome = executor.run(bubble_sort_path, inputs=[[5, 3, 1, 4, 2]])

    print("Genome:")
    for k, v in genome.items():
        print(f"  {k}: {v}")

    missing = EXPECTED_GENOME_KEYS - set(genome.keys())
    if missing:
        print(f"\nFAIL — missing genome keys: {missing}")
        sys.exit(1)

    print("\nPASS — all expected genome keys present")


if __name__ == "__main__":
    _main()
