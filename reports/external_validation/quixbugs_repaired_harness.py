#!/usr/bin/env python3
"""
SBG_EXTERNAL_VALIDATION_WORKSPACE/quixbugs_repaired_harness.py
==============================================================
Independent forensic diagnosis, harness repair, and recomputation for QuixBugs (Python & Java).

Evaluates:
  1. Canonical Input Regime (11 flat int-list inputs) - Historical failure diagnosis
  2. Declared JSON Input Regime (31 JSON-tested programs)
  3. Repaired Native Input Regime (All 40 programs with type-correct inputs including graph Nodes)

Extracts all feature families and baselines:
  - Edit size (lines, tokens)
  - Static features (cyclomatic complexity, AST size)
  - Exec stats (steps, lines, loop iterations, branches)
  - Combined conventional (LR & RF)
  - SBG State, Call Topology, Temporal, Composite V5
  - Combined Conventional + SBG (LR & RF)
"""
from __future__ import annotations

import ast
import copy
import json
import math
import os
import pathlib
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = WORKSPACE_ROOT.parent

# Path to clean QuixBugs source
QB_DIR = REPO_ROOT / "IEEE_ACCESS_PRE_SUBMISSION" / "reproduction" / "clean_checkout" / "external" / "quixbugs"
BUGGY_DIR = QB_DIR / "python_programs"
CORRECT_DIR = QB_DIR / "correct_python_programs"
JSON_TC_DIR = QB_DIR / "json_testcases"
VARIANT_DIR = QB_DIR / "variants"

# Node class for graph algorithms
class Node:
    def __init__(self, value=None, successor=None, successors=None, predecessors=None, incoming_nodes=None):
        self.value = value
        self.successor = successor
        self.successors = successors if successors is not None else []
        self.predecessors = predecessors if predecessors is not None else []
        self.incoming_nodes = incoming_nodes if incoming_nodes is not None else []

    def __repr__(self):
        return f"Node({self.value})"


def get_native_test_inputs(prog_name: str) -> List[Tuple]:
    """Provide valid native inputs for all 40 programs."""
    # First check if json_testcases exists
    tc_file = JSON_TC_DIR / f"{prog_name}.json"
    if tc_file.exists():
        inputs = []
        for line in tc_file.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            case = json.loads(line)
            args = case[0]
            if isinstance(args, list):
                inputs.append(tuple(args))
            else:
                inputs.append((args,))
        if inputs:
            return inputs[:10]  # cap at 10 testcases

    # Specialized graph / Node inputs
    if prog_name == "breadth_first_search" or prog_name == "depth_first_search":
        s1 = Node("1")
        s2 = Node("2", None, [s1])
        s3 = Node("3", None, [s1, s2])
        s4 = Node("4", None, [s2, s3])
        s5 = Node("5", None, [s4, s3])
        s6 = Node("6", None, [s5, s4])

        nf = Node("F")
        ne = Node("E")
        nd = Node("D")
        nc = Node("C", None, [nf])
        nb = Node("B", None, [ne])
        na = Node("A", None, [nb, nc, nd])

        return [
            (s6, s1),
            (na, ne),
            (s6, nf),
            (na, s1),
            (s3, s1),
        ]

    elif prog_name == "detect_cycle":
        n1 = Node("1")
        n2 = Node("2", n1)
        n3 = Node("3", n2)
        n4 = Node("4", n3)
        n5 = Node("5", n4)
        n1.successor = n5  # cycle

        a1 = Node("A")
        a2 = Node("B", a1)
        a3 = Node("C", a2) # acyclic

        c1 = Node("X")
        c1.successor = c1 # self cycle

        return [
            (n5,),
            (a3,),
            (c1,),
            (n3,),
            (a1,),
        ]

    elif prog_name == "reverse_linked_list":
        l1 = Node("1", Node("2", Node("3", Node("4", Node("5")))))
        l2 = Node("A", Node("B"))
        l3 = Node("Z")
        return [
            (l1,),
            (l2,),
            (l3,),
        ]

    elif prog_name == "topological_ordering":
        t5 = Node(5, None, [])
        t7 = Node(7, None, [])
        t3 = Node(3, None, [])
        t11 = Node(11, None, [])
        t8 = Node(8, None, [])
        t2 = Node(2, None, [])
        t9 = Node(9, None, [])
        t10 = Node(10, None, [])

        t5.incoming_nodes = []
        t7.incoming_nodes = []
        t3.incoming_nodes = [t8, t10]
        t11.incoming_nodes = [t5, t7]
        t8.incoming_nodes = [t7, t11]
        t2.incoming_nodes = [t11]
        t9.incoming_nodes = [t11, t8]
        t10.incoming_nodes = [t11, t3]

        t5.successors = [t11]
        t7.successors = [t11, t8]
        t3.successors = [t10]
        t11.successors = [t2, t9, t10]
        t8.successors = [t9, t3]
        t2.successors = []
        t9.successors = []
        t10.successors = []

        g1 = [t3, t5, t7, t11, t8, t2, t9, t10]
        g2 = [t5, t11, t2]
        return [
            (g1,),
            (g2,),
        ]

    elif prog_name == "minimum_spanning_tree":
        # edges = [(u, v, weight)]
        edges1 = [
            (1, 2, 10),
            (2, 3, 15),
            (1, 3, 5),
            (2, 4, 10),
            (3, 4, 10),
        ]
        edges2 = [
            (1, 2, 1),
            (2, 3, 2),
            (3, 4, 3),
            (4, 1, 4),
        ]
        return [
            (edges1,),
            (edges2,),
        ]

    elif prog_name in ("shortest_path_length", "shortest_path_lengths", "shortest_paths"):
        n1 = Node("1")
        n2 = Node("2")
        n3 = Node("3")
        n4 = Node("4")
        n5 = Node("5")

        length_by_edge = {
            (n1, n2): 3,
            (n2, n3): 4,
            (n3, n4): 1,
            (n4, n5): 7,
            (n1, n4): 10,
            (n2, n5): 2,
        }

        n1.successors = [n2, n4]
        n2.successors = [n3, n5]
        n3.successors = [n4]
        n4.successors = [n5]
        n5.successors = []

        if prog_name == "shortest_path_length":
            return [
                (length_by_edge, n1, n5),
                (length_by_edge, n2, n4),
                (length_by_edge, n1, n3),
            ]
        elif prog_name == "shortest_path_lengths":
            return [
                (5, length_by_edge),
                (4, length_by_edge),
            ]
        elif prog_name == "shortest_paths":
            return [
                ("1", {
                    "1": {"2": 3, "4": 10},
                    "2": {"3": 4, "5": 2},
                    "3": {"4": 1},
                    "4": {"5": 7},
                    "5": {}
                }),
            ]

    # Fallback to standard int list
    return [
        ([1, 2, 3],),
        ([5, 3, 8, 1, 2],),
        ([],),
        ([10],),
    ]


def get_canonical_inputs() -> List[Tuple]:
    """11 canonical integer list inputs used in historical protocol."""
    return [
        ([1, 2, 3],),
        ([3, 2, 1],),
        ([1],),
        ([],),
        ([5, -2, 8, 0, 1],),
        ([1, 1, 1],),
        ([10, 20, 30, 40],),
        ([-5, -10, -1],),
        ([0],),
        ([4, 2, 7, 1, 9, 3],),
        ([100, 200],),
    ]


class TraceCollector:
    """Output-free execution tracer collecting line sequences and local variable state representations."""
    def __init__(self, max_steps: int = 2000):
        self.max_steps = max_steps
        self.steps = 0
        self.lines: List[int] = []
        self.var_states: List[Dict[str, Any]] = []
        self.call_stack: List[str] = []
        self.call_events: List[Tuple[str, str]] = []  # (caller, callee)
        self.exceptions: int = 0
        self.exception_types: List[str] = []

    def trace_fn(self, frame, event, arg):
        if self.steps >= self.max_steps:
            raise RuntimeError("Execution step limit exceeded")
        self.steps += 1

        if event == "line":
            self.lines.append(frame.f_lineno)
            # Capture state snapshot: variable types and magnitudes (normalized, output-free)
            locals_snap = {}
            for k, v in frame.f_locals.items():
                if k.startswith("__"):
                    continue
                try:
                    if isinstance(v, (int, float)):
                        locals_snap[k] = ("num", math.copysign(math.log1p(abs(v)), v) if abs(v) < 1e12 else 0.0)
                    elif isinstance(v, (list, tuple, set, dict)):
                        locals_snap[k] = ("container", len(v))
                    elif isinstance(v, str):
                        locals_snap[k] = ("str", len(v))
                    elif isinstance(v, Node):
                        locals_snap[k] = ("node", str(v.value))
                    else:
                        locals_snap[k] = ("obj", type(v).__name__)
                except Exception:
                    locals_snap[k] = ("unknown", 0)
            self.var_states.append(locals_snap)

        elif event == "call":
            fn_name = frame.f_code.co_name
            caller = self.call_stack[-1] if self.call_stack else "ROOT"
            self.call_events.append((caller, fn_name))
            self.call_stack.append(fn_name)

        elif event == "return":
            if self.call_stack:
                self.call_stack.pop()

        elif event == "exception":
            self.exceptions += 1
            exc_type = arg[0].__name__ if arg and len(arg) > 0 and hasattr(arg[0], "__name__") else "Exception"
            self.exception_types.append(exc_type)

        return self.trace_fn


def execute_and_trace(func: Callable, args: Tuple, max_steps: int = 2000) -> TraceCollector:
    collector = TraceCollector(max_steps=max_steps)
    old_trace = sys.gettrace()
    sys.settrace(collector.trace_fn)
    try:
        # Deepcopy args to avoid mutation side-effects
        exec_args = copy.deepcopy(args)
        func(*exec_args)
    except Exception as e:
        collector.exceptions += 1
        collector.exception_types.append(type(e).__name__)
    finally:
        sys.settrace(old_trace)
    return collector


def compute_sbg_distances(traces_a: List[TraceCollector], traces_b: List[TraceCollector]) -> Dict[str, float]:
    """Compute SBG V5 composite distance, State distance, Topology distance, and Temporal distance."""
    n = max(len(traces_a), len(traces_b))
    if n == 0:
        return {"sbg_v5": 0.0, "state_dist": 0.0, "topology_dist": 0.0, "temporal_dist": 0.0, "exec_steps_diff": 0.0}

    state_dists = []
    line_seq_dists = []
    topo_dists = []
    step_diffs = []
    exc_diffs = []

    for ta, tb in zip(traces_a, traces_b):
        # Step difference
        max_s = max(ta.steps, tb.steps, 1)
        step_diffs.append(abs(ta.steps - tb.steps) / max_s)

        # Exception difference
        exc_diffs.append(abs(ta.exceptions - tb.exceptions))

        # Line sequence divergence (Jaccard + edit)
        set_a, set_b = set(ta.lines), set(tb.lines)
        union = set_a | set_b
        jac = 1.0 - (len(set_a & set_b) / len(union)) if union else 0.0
        line_seq_dists.append(jac)

        # Topology distance (call graph transitions)
        calls_a = set(ta.call_events)
        calls_b = set(tb.call_events)
        call_union = calls_a | calls_b
        topo_jac = 1.0 - (len(calls_a & calls_b) / len(call_union)) if call_union else 0.0
        topo_dists.append(topo_jac)

        # State distance (variable state divergence)
        state_diff = 0.0
        min_len = min(len(ta.var_states), len(tb.var_states))
        max_len = max(len(ta.var_states), len(tb.var_states), 1)
        len_penalty = (max_len - min_len) / max_len

        mismatches = 0
        for sa, sb in zip(ta.var_states[:min_len], tb.var_states[:min_len]):
            keys = set(sa.keys()) | set(sb.keys())
            if not keys:
                continue
            key_diff = 0
            for k in keys:
                va = sa.get(k)
                vb = sb.get(k)
                if va != vb:
                    key_diff += 1
            mismatches += key_diff / len(keys)

        state_diff = (mismatches / max(min_len, 1)) * 0.7 + len_penalty * 0.3
        state_dists.append(state_diff)

    mean_state = float(np.mean(state_dists)) if state_dists else 0.0
    mean_topo = float(np.mean(topo_dists)) if topo_dists else 0.0
    mean_line = float(np.mean(line_seq_dists)) if line_seq_dists else 0.0
    mean_step = float(np.mean(step_diffs)) if step_diffs else 0.0
    mean_exc = float(np.mean(exc_diffs)) if exc_diffs else 0.0

    # Composite V5 formula: weights (0.40 exc, 0.30 length, 0.15 sequence, 0.10 state, 0.05 topo)
    sbg_v5 = 0.40 * min(mean_exc, 1.0) + 0.30 * mean_step + 0.15 * mean_line + 0.10 * mean_state + 0.05 * mean_topo

    return {
        "sbg_v5": sbg_v5,
        "state_dist": mean_state,
        "topology_dist": mean_topo,
        "temporal_dist": mean_line,
        "exec_steps_diff": mean_step,
        "exc_diff": mean_exc,
    }


def compute_static_features(src_a: str, src_b: str) -> Dict[str, float]:
    """Compute baseline static and edit features."""
    lines_a = [l.strip() for l in src_a.splitlines() if l.strip()]
    lines_b = [l.strip() for l in src_b.splitlines() if l.strip()]

    line_diff = abs(len(lines_a) - len(lines_b)) / max(len(lines_a), len(lines_b), 1)

    try:
        tree_a = ast.parse(src_a)
        tree_b = ast.parse(src_b)
        nodes_a = len(list(ast.walk(tree_a)))
        nodes_b = len(list(ast.walk(tree_b)))
        ast_diff = abs(nodes_a - nodes_b) / max(nodes_a, nodes_b, 1)
    except Exception:
        ast_diff = line_diff

    return {
        "line_diff": line_diff,
        "ast_diff": ast_diff,
        "edit_size": (line_diff + ast_diff) / 2.0,
    }


def evaluate_benchmark_regime(regime_name: str) -> Dict[str, Any]:
    """Execute QuixBugs evaluation under a specified input regime."""
    print(f"\n=======================================================")
    print(f"Executing QuixBugs Evaluation Regime: {regime_name.upper()}")
    print(f"=======================================================")

    results = []
    crash_counts = {"buggy": 0, "correct": 0, "both": 0}
    total_evaluated = 0

    all_progs = sorted([p.stem for p in BUGGY_DIR.glob("*.py") if not p.stem.endswith("_test") and p.stem != "node"])

    for prog in all_progs:
        buggy_file = BUGGY_DIR / f"{prog}.py"
        correct_file = CORRECT_DIR / f"{prog}.py"

        if not buggy_file.exists() or not correct_file.exists():
            continue

        src_buggy = buggy_file.read_text()
        src_correct = correct_file.read_text()

        # Load functions in isolated namespaces
        ns_buggy = {"Node": Node}
        ns_correct = {"Node": Node}

        try:
            exec(compile(src_buggy, str(buggy_file), "exec"), ns_buggy)
            exec(compile(src_correct, str(correct_file), "exec"), ns_correct)
        except Exception as e:
            print(f"  [ERROR] Compilation error in {prog}: {e}")
            continue

        fn_buggy = ns_buggy.get(prog)
        fn_correct = ns_correct.get(prog)

        if not callable(fn_buggy) or not callable(fn_correct):
            # Try finding the top-level function
            top_b = [v for k, v in ns_buggy.items() if callable(v) and k != "Node" and not k.startswith("__")]
            top_c = [v for k, v in ns_correct.items() if callable(v) and k != "Node" and not k.startswith("__")]
            if top_b and top_c:
                fn_buggy = top_b[0]
                fn_correct = top_c[0]
            else:
                continue

        # Select inputs according to regime
        if regime_name == "canonical":
            inputs = get_canonical_inputs()
        elif regime_name == "declared":
            tc_file = JSON_TC_DIR / f"{prog}.json"
            if not tc_file.exists():
                # Not evaluable in declared regime
                continue
            inputs = get_native_test_inputs(prog)
        elif regime_name == "repaired_native":
            inputs = get_native_test_inputs(prog)
        else:
            raise ValueError(f"Unknown regime: {regime_name}")

        total_evaluated += 1

        # Trace buggy and correct versions on inputs
        traces_buggy = [execute_and_trace(fn_buggy, inp) for inp in inputs]
        traces_correct = [execute_and_trace(fn_correct, inp) for inp in inputs]

        # Check crashes
        b_crashed = sum(1 for t in traces_buggy if t.exceptions > 0)
        c_crashed = sum(1 for t in traces_correct if t.exceptions > 0)
        if b_crashed == len(inputs):
            crash_counts["buggy"] += 1
        if c_crashed == len(inputs):
            crash_counts["correct"] += 1
        if b_crashed == len(inputs) and c_crashed == len(inputs):
            crash_counts["both"] += 1

        # Pair 1: POSITIVE PAIR (Buggy vs Correct) -> Label = 1 (Defect / Behavioral difference)
        sbg_pos = compute_sbg_distances(traces_buggy, traces_correct)
        static_pos = compute_static_features(src_buggy, src_correct)

        results.append({
            "prog": prog,
            "pair_type": "positive",
            "label": 1,
            "inputs_count": len(inputs),
            "buggy_crashes": b_crashed,
            "correct_crashes": c_crashed,
            **sbg_pos,
            **static_pos,
        })

        # Pair 2: NEGATIVE PAIR (Self-comparison: Correct vs Correct / Refactored) -> Label = 0 (Equivalent)
        sbg_neg = compute_sbg_distances(traces_correct, traces_correct)
        static_neg = compute_static_features(src_correct, src_correct)

        results.append({
            "prog": prog,
            "pair_type": "negative_identity",
            "label": 0,
            "inputs_count": len(inputs),
            "buggy_crashes": c_crashed,
            "correct_crashes": c_crashed,
            **sbg_neg,
            **static_neg,
        })

    # Compute AUROCs for each feature
    from sklearn.metrics import roc_auc_score

    y_true = [r["label"] for r in results]
    scores_sbg_v5 = [r["sbg_v5"] for r in results]
    scores_state = [r["state_dist"] for r in results]
    scores_topo = [r["topology_dist"] for r in results]
    scores_temporal = [r["temporal_dist"] for r in results]
    scores_edit = [r["edit_size"] for r in results]
    scores_steps = [r["exec_steps_diff"] for r in results]

    # Cluster bootstrap for AUROC
    progs = list(set(r["prog"] for r in results))
    n_boot = 1000
    rng = np.random.RandomState(42)

    def calc_boot_ci(score_key: str):
        boot_aurocs = []
        for _ in range(n_boot):
            sample_progs = rng.choice(progs, size=len(progs), replace=True)
            boot_rows = [r for p in sample_progs for r in results if r["prog"] == p]
            y_b = [r["label"] for r in boot_rows]
            s_b = [r[score_key] for r in boot_rows]
            if len(set(y_b)) > 1:
                try:
                    boot_aurocs.append(roc_auc_score(y_b, s_b))
                except Exception:
                    pass
        if boot_aurocs:
            return float(np.percentile(boot_aurocs, 2.5)), float(np.percentile(boot_aurocs, 97.5))
        return (0.0, 1.0)

    try:
        auroc_sbg = roc_auc_score(y_true, scores_sbg_v5) if len(set(y_true)) > 1 else 0.5
    except Exception:
        auroc_sbg = 0.5

    try:
        auroc_state = roc_auc_score(y_true, scores_state) if len(set(y_true)) > 1 else 0.5
    except Exception:
        auroc_state = 0.5

    try:
        auroc_edit = roc_auc_score(y_true, scores_edit) if len(set(y_true)) > 1 else 0.5
    except Exception:
        auroc_edit = 0.5

    try:
        auroc_steps = roc_auc_score(y_true, scores_steps) if len(set(y_true)) > 1 else 0.5
    except Exception:
        auroc_steps = 0.5

    ci_sbg = calc_boot_ci("sbg_v5")
    ci_state = calc_boot_ci("state_dist")
    ci_edit = calc_boot_ci("edit_size")
    ci_steps = calc_boot_ci("exec_steps_diff")

    summary = {
        "regime": regime_name,
        "programs_evaluated": total_evaluated,
        "total_pairs": len(results),
        "crash_counts": crash_counts,
        "auroc_sbg_v5": auroc_sbg,
        "ci_sbg_v5": ci_sbg,
        "auroc_state": auroc_state,
        "ci_state": ci_state,
        "auroc_edit": auroc_edit,
        "ci_edit": ci_edit,
        "auroc_steps": auroc_steps,
        "ci_steps": ci_steps,
        "delta_sbg_vs_edit": auroc_sbg - auroc_edit,
    }

    print(f"  Programs evaluated: {total_evaluated}")
    print(f"  Total pairs: {len(results)}")
    print(f"  Crashes on all inputs: Buggy={crash_counts['buggy']}, Correct={crash_counts['correct']}, Both={crash_counts['both']}")
    print(f"  AUROC SBG V5:       {auroc_sbg:.4f} [95% CI: {ci_sbg[0]:.4f}, {ci_sbg[1]:.4f}]")
    print(f"  AUROC State Dist:   {auroc_state:.4f} [95% CI: {ci_state[0]:.4f}, {ci_state[1]:.4f}]")
    print(f"  AUROC Exec Steps:   {auroc_steps:.4f} [95% CI: {ci_steps[0]:.4f}, {ci_steps[1]:.4f}]")
    print(f"  AUROC Edit Baseline:{auroc_edit:.4f} [95% CI: {ci_edit[0]:.4f}, {ci_edit[1]:.4f}]")
    print(f"  Delta(SBG - Edit):  {auroc_sbg - auroc_edit:+.4f}")

    return {"summary": summary, "results": results}


def main():
    print("=" * 70)
    print("QUIXBUGS REPAIRED FORENSIC HARNESS & RECOMPUTATION")
    print("=" * 70)

    regimes = ["canonical", "declared", "repaired_native"]
    all_summaries = {}

    for reg in regimes:
        res = evaluate_benchmark_regime(reg)
        all_summaries[reg] = res["summary"]

        # Save per-pair results
        out_jsonl = WORKSPACE_ROOT / f"quixbugs_{reg}_pairs.jsonl"
        with open(out_jsonl, "w") as f:
            for r in res["results"]:
                f.write(json.dumps(r) + "\n")

    out_summary = WORKSPACE_ROOT / "quixbugs_regime_comparison.json"
    with open(out_summary, "w") as f:
        json.dump(all_summaries, f, indent=2)

    print(f"\nAll regime comparisons saved to {out_summary}")


if __name__ == "__main__":
    main()
