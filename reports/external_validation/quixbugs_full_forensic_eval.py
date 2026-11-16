#!/usr/bin/env python3
"""
SBG_EXTERNAL_VALIDATION_WORKSPACE/quixbugs_full_forensic_eval.py
===============================================================
Comprehensive QuixBugs Forensic Evaluation with full SP Variant Negatives.
Evaluates Canonical vs Declared vs Repaired Native across all baseline families.
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
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = WORKSPACE_ROOT.parent

QB_DIR = REPO_ROOT / "IEEE_ACCESS_PRE_SUBMISSION" / "reproduction" / "clean_checkout" / "external" / "quixbugs"
BUGGY_DIR = QB_DIR / "python_programs"
CORRECT_DIR = QB_DIR / "correct_python_programs"
JSON_TC_DIR = QB_DIR / "json_testcases"
VARIANT_DIR = QB_DIR / "variants"

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
            return inputs[:10]

    if prog_name in ("breadth_first_search", "depth_first_search"):
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

        return [(s6, s1), (na, ne), (s6, nf), (na, s1), (s3, s1)]

    elif prog_name == "detect_cycle":
        n1 = Node("1")
        n2 = Node("2", n1)
        n3 = Node("3", n2)
        n4 = Node("4", n3)
        n5 = Node("5", n4)
        n1.successor = n5

        a1 = Node("A")
        a2 = Node("B", a1)
        a3 = Node("C", a2)

        c1 = Node("X")
        c1.successor = c1

        return [(n5,), (a3,), (c1,), (n3,), (a1,)]

    elif prog_name == "reverse_linked_list":
        l1 = Node("1", Node("2", Node("3", Node("4", Node("5")))))
        l2 = Node("A", Node("B"))
        l3 = Node("Z")
        return [(l1,), (l2,), (l3,)]

    elif prog_name == "topological_ordering":
        t5, t7, t3, t11 = Node(5), Node(7), Node(3), Node(11)
        t8, t2, t9, t10 = Node(8), Node(2), Node(9), Node(10)

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

        return [([t3, t5, t7, t11, t8, t2, t9, t10],), ([t5, t11, t2],)]

    elif prog_name == "minimum_spanning_tree":
        edges1 = [(1, 2, 10), (2, 3, 15), (1, 3, 5), (2, 4, 10), (3, 4, 10)]
        edges2 = [(1, 2, 1), (2, 3, 2), (3, 4, 3), (4, 1, 4)]
        return [(edges1,), (edges2,)]

    elif prog_name in ("shortest_path_length", "shortest_path_lengths", "shortest_paths"):
        n1, n2, n3, n4, n5 = Node("1"), Node("2"), Node("3"), Node("4"), Node("5")
        lbe = {(n1, n2): 3, (n2, n3): 4, (n3, n4): 1, (n4, n5): 7, (n1, n4): 10, (n2, n5): 2}
        n1.successors = [n2, n4]
        n2.successors = [n3, n5]
        n3.successors = [n4]
        n4.successors = [n5]

        if prog_name == "shortest_path_length":
            return [(lbe, n1, n5), (lbe, n2, n4), (lbe, n1, n3)]
        elif prog_name == "shortest_path_lengths":
            return [(5, lbe), (4, lbe)]
        elif prog_name == "shortest_paths":
            return [("1", {"1": {"2": 3, "4": 10}, "2": {"3": 4, "5": 2}, "3": {"4": 1}, "4": {"5": 7}, "5": {}})]

    return [([1, 2, 3],), ([5, 3, 8, 1, 2],), ([],), ([10],)]


def get_canonical_inputs() -> List[Tuple]:
    return [
        ([1, 2, 3],), ([3, 2, 1],), ([1],), ([],), ([5, -2, 8, 0, 1],),
        ([1, 1, 1],), ([10, 20, 30, 40],), ([-5, -10, -1],), ([0],),
        ([4, 2, 7, 1, 9, 3],), ([100, 200],)
    ]


class TraceCollector:
    def __init__(self, max_steps: int = 2000):
        self.max_steps = max_steps
        self.steps = 0
        self.lines: List[int] = []
        self.var_states: List[Dict[str, Any]] = []
        self.call_events: List[Tuple[str, str]] = []
        self.call_stack: List[str] = []
        self.exceptions: int = 0

    def trace_fn(self, frame, event, arg):
        if self.steps >= self.max_steps:
            raise RuntimeError("Execution step limit exceeded")
        self.steps += 1

        if event == "line":
            self.lines.append(frame.f_lineno)
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

        return self.trace_fn


def execute_and_trace(func: Callable, args: Tuple, max_steps: int = 2000) -> TraceCollector:
    collector = TraceCollector(max_steps=max_steps)
    old_trace = sys.gettrace()
    sys.settrace(collector.trace_fn)
    try:
        exec_args = copy.deepcopy(args)
        func(*exec_args)
    except Exception:
        collector.exceptions += 1
    finally:
        sys.settrace(old_trace)
    return collector


def compute_sbg_distances(traces_a: List[TraceCollector], traces_b: List[TraceCollector]) -> Dict[str, float]:
    n = max(len(traces_a), len(traces_b))
    if n == 0:
        return {"sbg_v5": 0.0, "state_dist": 0.0, "topology_dist": 0.0, "temporal_dist": 0.0, "exec_steps_diff": 0.0, "exc_diff": 0.0}

    state_dists, line_seq_dists, topo_dists, step_diffs, exc_diffs = [], [], [], [], []

    for ta, tb in zip(traces_a, traces_b):
        max_s = max(ta.steps, tb.steps, 1)
        step_diffs.append(abs(ta.steps - tb.steps) / max_s)
        exc_diffs.append(abs(ta.exceptions - tb.exceptions))

        set_a, set_b = set(ta.lines), set(tb.lines)
        union = set_a | set_b
        jac = 1.0 - (len(set_a & set_b) / len(union)) if union else 0.0
        line_seq_dists.append(jac)

        calls_a = set(ta.call_events)
        calls_b = set(tb.call_events)
        call_union = calls_a | calls_b
        topo_jac = 1.0 - (len(calls_a & calls_b) / len(call_union)) if call_union else 0.0
        topo_dists.append(topo_jac)

        min_len = min(len(ta.var_states), len(tb.var_states))
        max_len = max(len(ta.var_states), len(tb.var_states), 1)
        len_penalty = (max_len - min_len) / max_len

        mismatches = 0
        for sa, sb in zip(ta.var_states[:min_len], tb.var_states[:min_len]):
            keys = set(sa.keys()) | set(sb.keys())
            if not keys:
                continue
            key_diff = sum(1 for k in keys if sa.get(k) != sb.get(k))
            mismatches += key_diff / len(keys)

        state_diff = (mismatches / max(min_len, 1)) * 0.7 + len_penalty * 0.3
        state_dists.append(state_diff)

    mean_state = float(np.mean(state_dists)) if state_dists else 0.0
    mean_topo = float(np.mean(topo_dists)) if topo_dists else 0.0
    mean_line = float(np.mean(line_seq_dists)) if line_seq_dists else 0.0
    mean_step = float(np.mean(step_diffs)) if step_diffs else 0.0
    mean_exc = float(np.mean(exc_diffs)) if exc_diffs else 0.0

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


def load_function(src: str, filepath: pathlib.Path, expected_name: str) -> Optional[Callable]:
    ns = {"Node": Node}
    try:
        exec(compile(src, str(filepath), "exec"), ns)
    except Exception:
        return None
    fn = ns.get(expected_name)
    if callable(fn):
        return fn
    top = [v for k, v in ns.items() if callable(v) and k != "Node" and not k.startswith("__")]
    return top[0] if top else None


def run_full_evaluation(regime: str, include_sp2: bool = True) -> Dict[str, Any]:
    print(f"\nEvaluating QuixBugs Regime: {regime} (Include SP-2: {include_sp2})")
    all_progs = sorted([p.stem for p in BUGGY_DIR.glob("*.py") if not p.stem.endswith("_test") and p.stem != "node"])

    pairs = []
    for prog in all_progs:
        buggy_file = BUGGY_DIR / f"{prog}.py"
        correct_file = CORRECT_DIR / f"{prog}.py"

        if not buggy_file.exists() or not correct_file.exists():
            continue

        src_buggy = buggy_file.read_text()
        src_correct = correct_file.read_text()

        fn_buggy = load_function(src_buggy, buggy_file, prog)
        fn_correct = load_function(src_correct, correct_file, prog)

        if not fn_buggy or not fn_correct:
            continue

        if regime == "canonical":
            inputs = get_canonical_inputs()
        elif regime == "declared":
            tc_file = JSON_TC_DIR / f"{prog}.json"
            if not tc_file.exists():
                continue
            inputs = get_native_test_inputs(prog)
        elif regime == "repaired_native":
            inputs = get_native_test_inputs(prog)
        else:
            raise ValueError(f"Unknown regime: {regime}")

        # Traces
        traces_buggy = [execute_and_trace(fn_buggy, inp) for inp in inputs]
        traces_correct = [execute_and_trace(fn_correct, inp) for inp in inputs]

        # 1. Positive pair (Buggy vs Correct)
        sbg_pos = compute_sbg_distances(traces_buggy, traces_correct)
        static_pos = compute_static_features(src_buggy, src_correct)
        pairs.append({
            "prog": prog,
            "pair_type": "positive_real_bug",
            "label": 1,
            **sbg_pos,
            **static_pos,
        })

        # 2. Negative pair (Correct vs SP-Variants)
        sp_files = sorted(VARIANT_DIR.glob(f"{prog}__sp-*.py"))
        for sp_file in sp_files:
            variant_type = sp_file.stem.split("__")[1]
            if not include_sp2 and variant_type.startswith("sp-2"):
                continue

            src_sp = sp_file.read_text()
            fn_sp = load_function(src_sp, sp_file, prog)
            if not fn_sp:
                continue

            traces_sp = [execute_and_trace(fn_sp, inp) for inp in inputs]
            sbg_neg = compute_sbg_distances(traces_correct, traces_sp)
            static_neg = compute_static_features(src_correct, src_sp)

            pairs.append({
                "prog": prog,
                "pair_type": f"negative_{variant_type}",
                "label": 0,
                **sbg_neg,
                **static_neg,
            })

    # Evaluate all models & baselines
    y = np.array([p["label"] for p in pairs])
    progs = np.array([p["prog"] for p in pairs])
    unique_progs = sorted(list(set(progs)))

    # Feature matrices
    X_edit = np.array([[p["line_diff"], p["ast_diff"]] for p in pairs])
    X_static = np.array([[p["edit_size"]] for p in pairs])
    X_exec = np.array([[p["exec_steps_diff"], p["exc_diff"]] for p in pairs])
    X_conv = np.hstack([X_edit, X_exec])
    X_sbg = np.array([[p["sbg_v5"], p["state_dist"], p["topology_dist"], p["temporal_dist"]] for p in pairs])
    X_full = np.hstack([X_conv, X_sbg])

    # Leave-One-Program-Out Cross-Validation (Project/Program Disjoint)
    y_pred_lr_conv = np.zeros(len(y))
    y_pred_lr_sbg = np.zeros(len(y))
    y_pred_lr_full = np.zeros(len(y))
    y_pred_rf_conv = np.zeros(len(y))
    y_pred_rf_full = np.zeros(len(y))

    for p_out in unique_progs:
        train_idx = (progs != p_out)
        test_idx = (progs == p_out)

        if len(set(y[train_idx])) < 2 or sum(test_idx) == 0:
            continue

        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import make_pipeline

        # LR Conventional
        pipe_c = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500, random_state=42))
        pipe_c.fit(X_conv[train_idx], y[train_idx])
        y_pred_lr_conv[test_idx] = pipe_c.predict_proba(X_conv[test_idx])[:, 1]

        # LR SBG alone
        pipe_s = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500, random_state=42))
        pipe_s.fit(X_sbg[train_idx], y[train_idx])
        y_pred_lr_sbg[test_idx] = pipe_s.predict_proba(X_sbg[test_idx])[:, 1]

        # LR Full (Conv + SBG)
        pipe_f = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500, random_state=42))
        pipe_f.fit(X_full[train_idx], y[train_idx])
        y_pred_lr_full[test_idx] = pipe_f.predict_proba(X_full[test_idx])[:, 1]

        # RF Conventional
        rf_c = RandomForestClassifier(n_estimators=100, max_depth=3, random_state=42).fit(X_conv[train_idx], y[train_idx])
        y_pred_rf_conv[test_idx] = rf_c.predict_proba(X_conv[test_idx])[:, 1]

        # RF Full
        rf_f = RandomForestClassifier(n_estimators=100, max_depth=3, random_state=42).fit(X_full[train_idx], y[train_idx])
        y_pred_rf_full[test_idx] = rf_f.predict_proba(X_full[test_idx])[:, 1]

    # AUROCs
    auroc_sbg_raw = roc_auc_score(y, [p["sbg_v5"] for p in pairs])
    auroc_state_raw = roc_auc_score(y, [p["state_dist"] for p in pairs])
    auroc_edit_raw = roc_auc_score(y, [p["edit_size"] for p in pairs])
    auroc_lr_conv = roc_auc_score(y, y_pred_lr_conv)
    auroc_lr_sbg = roc_auc_score(y, y_pred_lr_sbg)
    auroc_lr_full = roc_auc_score(y, y_pred_lr_full)
    auroc_rf_conv = roc_auc_score(y, y_pred_rf_conv)
    auroc_rf_full = roc_auc_score(y, y_pred_rf_full)

    # Cluster Bootstrap CI for primary metrics
    rng = np.random.RandomState(42)
    boot_sbg, boot_conv, boot_full, boot_delta = [], [], [], []
    for _ in range(1000):
        sampled_p = rng.choice(unique_progs, size=len(unique_progs), replace=True)
        b_idx = [i for p in sampled_p for i, prog in enumerate(progs) if prog == p]
        y_b = y[b_idx]
        if len(set(y_b)) < 2:
            continue
        try:
            auc_s = roc_auc_score(y_b, [pairs[i]["sbg_v5"] for i in b_idx])
            auc_c = roc_auc_score(y_b, y_pred_lr_conv[b_idx])
            auc_f = roc_auc_score(y_b, y_pred_lr_full[b_idx])
            boot_sbg.append(auc_s)
            boot_conv.append(auc_c)
            boot_full.append(auc_f)
            boot_delta.append(auc_f - auc_c)
        except Exception:
            pass

    ci_sbg = (float(np.percentile(boot_sbg, 2.5)), float(np.percentile(boot_sbg, 97.5))) if boot_sbg else (0.0, 1.0)
    ci_conv = (float(np.percentile(boot_conv, 2.5)), float(np.percentile(boot_conv, 97.5))) if boot_conv else (0.0, 1.0)
    ci_full = (float(np.percentile(boot_full, 2.5)), float(np.percentile(boot_full, 97.5))) if boot_full else (0.0, 1.0)
    ci_delta = (float(np.percentile(boot_delta, 2.5)), float(np.percentile(boot_delta, 97.5))) if boot_delta else (-1.0, 1.0)

    print(f"  Total Pairs: {len(pairs)} (Positives: {sum(y==1)}, Negatives: {sum(y==0)})")
    print(f"  AUROC SBG V5 Raw:          {auroc_sbg_raw:.4f} [95% CI: {ci_sbg[0]:.4f}, {ci_sbg[1]:.4f}]")
    print(f"  AUROC State Alone:         {auroc_state_raw:.4f}")
    print(f"  AUROC Edit Baseline Raw:   {auroc_edit_raw:.4f}")
    print(f"  AUROC LR Conventional:     {auroc_lr_conv:.4f} [95% CI: {ci_conv[0]:.4f}, {ci_conv[1]:.4f}]")
    print(f"  AUROC LR SBG Alone:        {auroc_lr_sbg:.4f}")
    print(f"  AUROC LR (Conv + SBG):     {auroc_lr_full:.4f} [95% CI: {ci_full[0]:.4f}, {ci_full[1]:.4f}]")
    print(f"  AUROC RF Conventional:     {auroc_rf_conv:.4f}")
    print(f"  AUROC RF (Conv + SBG):     {auroc_rf_full:.4f}")
    print(f"  Incremental Value (ΔLR):   {auroc_lr_full - auroc_lr_conv:+.4f} [95% CI: {ci_delta[0]:.4f}, {ci_delta[1]:.4f}]")

    return {
        "regime": regime,
        "include_sp2": include_sp2,
        "n_pairs": len(pairs),
        "n_pos": int(sum(y == 1)),
        "n_neg": int(sum(y == 0)),
        "auroc_sbg_raw": auroc_sbg_raw,
        "ci_sbg": ci_sbg,
        "auroc_state_raw": auroc_state_raw,
        "auroc_edit_raw": auroc_edit_raw,
        "auroc_lr_conv": auroc_lr_conv,
        "ci_conv": ci_conv,
        "auroc_lr_sbg": auroc_lr_sbg,
        "auroc_lr_full": auroc_lr_full,
        "ci_full": ci_full,
        "auroc_rf_conv": auroc_rf_conv,
        "auroc_rf_full": auroc_rf_full,
        "delta_lr": auroc_lr_full - auroc_lr_conv,
        "ci_delta": ci_delta,
        "pairs": pairs,
    }


def main():
    print("=" * 80)
    print("QUIXBUGS FULL FORENSIC EVALUATION & STATISTICAL RECOMPUTATION")
    print("=" * 80)

    configs = [
        ("canonical", True),
        ("canonical", False),
        ("declared", True),
        ("declared", False),
        ("repaired_native", True),
        ("repaired_native", False),
    ]

    results = {}
    for regime, include_sp2 in configs:
        tag = f"{regime}_{'all' if include_sp2 else 'ex_sp2'}"
        res = run_full_evaluation(regime, include_sp2)
        results[tag] = {k: v for k, v in res.items() if k != "pairs"}

        out_csv = WORKSPACE_ROOT / f"quixbugs_{tag}_pairs.csv"
        import pandas as pd
        pd.DataFrame(res["pairs"]).to_csv(out_csv, index=False)

    out_summary = WORKSPACE_ROOT / "quixbugs_full_recomputation_summary.json"
    with open(out_summary, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSummary successfully written to {out_summary}")


if __name__ == "__main__":
    main()
