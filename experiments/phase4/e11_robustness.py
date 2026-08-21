"""
experiments/phase4/e11_robustness.py
=======================================
E11: Noise/Partial-Trace Robustness.

Tests whether similarity scores are robust to implementation-level noise
that should NOT affect behavior — simulating partial/noisy program snapshots.

Noise levels applied to SOURCE CODE (since we don't have dynamic traces):
  Level 0: Original source (no noise)
  Level 1: Whitespace normalization noise (blank line additions/removals)
  Level 2: Comment injection (add meaningless comments — should NOT affect AST)
  Level 3: Variable suffix renaming (rename 20% of vars with _renamed suffix)
  Level 4: Dead code insertion (add unreachable branches — semantics-preserving)

For each noise level, re-score EQUIV pairs and measure:
- Mean similarity (should stay HIGH = stable)
- AUROC (should stay near Phase 3 value = stable discrimination)

Hypothesis addressed: H3 (robustness under implementation-preserving transforms)
"""
import ast
import json
import pathlib
import random
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from experiments.phase4.utils import ensure_token_initialized

from baselines.common import load_pairs, load_source, compute_auroc
from baselines.b02_ast import score_fn as ast_fn
from baselines.b01_token import score_fn as token_fn

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "phase4" / "E11"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
N_BOOTSTRAP = 500  # Reduced for speed — 4 noise levels × full test set


def bootstrap_ci_mean(values, n_resamples=N_BOOTSTRAP, seed=SEED):
    if len(values) < 2:
        return values[0] if values else 0.0, 0.0, 0.0
    rng = random.Random(seed)
    n = len(values)
    means = sorted([
        sum(values[rng.randint(0, n - 1)] for _ in range(n)) / n
        for _ in range(n_resamples)
    ])
    return sum(values) / n, means[int(0.025 * n_resamples)], means[int(0.975 * n_resamples)]


# ---------------------------------------------------------------------------
# Noise application functions
# ---------------------------------------------------------------------------

def apply_noise_level_0(source: str, seed: int = SEED) -> str:
    """No noise."""
    return source


def apply_noise_level_1(source: str, seed: int = SEED) -> str:
    """Whitespace noise: randomly add/remove blank lines."""
    rng = random.Random(seed)
    lines = source.splitlines()
    out = []
    for line in lines:
        if rng.random() < 0.1:
            out.append("")  # Insert blank line
        out.append(line)
    return "\n".join(out)


def apply_noise_level_2(source: str, seed: int = SEED) -> str:
    """Comment injection: add meaningless inline comments."""
    rng = random.Random(seed)
    comments = ["# ok", "# done", "# step", "# check", "# process"]
    lines = source.splitlines()
    out = []
    for line in lines:
        stripped = line.rstrip()
        if stripped and not stripped.lstrip().startswith("#") and rng.random() < 0.15:
            out.append(stripped + "  " + rng.choice(comments))
        else:
            out.append(line)
    return "\n".join(out)


def apply_noise_level_3(source: str, seed: int = SEED) -> str:
    """Rename 20% of local variable names with _noisy suffix."""
    rng = random.Random(seed)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source

    # Collect all Name nodes that are local variables (Store context)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)

    rename_set = set(
        n for n in names if rng.random() < 0.20
    )

    class Renamer(ast.NodeTransformer):
        def visit_Name(self, node):
            if node.id in rename_set:
                node.id = node.id + "_noisy"
            return node
        def visit_arg(self, node):
            if node.arg in rename_set:
                node.arg = node.arg + "_noisy"
            return node

    try:
        new_tree = Renamer().visit(tree)
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)
    except Exception:
        return source


def apply_noise_level_4(source: str, seed: int = SEED) -> str:
    """Dead code insertion: add unreachable branches."""
    rng = random.Random(seed)
    dead_snippets = [
        "\n    if False:\n        pass  # unreachable\n",
        "\n    if 0:\n        x = None  # dead\n",
    ]
    lines = source.splitlines()
    out = []
    in_function = False
    for line in lines:
        out.append(line)
        if line.strip().startswith("def "):
            in_function = True
        elif in_function and line.strip() and not line.startswith(" ") and not line.startswith("\t"):
            in_function = False
        elif in_function and line.strip().startswith("return ") and rng.random() < 0.1:
            # Insert dead code before return
            out.insert(-1, rng.choice(dead_snippets))
    return "\n".join(out)


NOISE_LEVELS = [
    (0, "Original", apply_noise_level_0),
    (1, "Whitespace", apply_noise_level_1),
    (2, "Comments", apply_noise_level_2),
    (3, "Var_rename_20pct", apply_noise_level_3),
    (4, "Dead_code", apply_noise_level_4),
]


def run_e11():
    print("=" * 60)
    print("E11: Noise/Partial-Trace Robustness")
    print("=" * 60)

    ensure_token_initialized()
    test_pairs = load_pairs("test")
    # Use a subset for speed — all test pairs but limit to first 300
    equiv_pairs = [p for p in test_pairs if p["semantic_relation"] == "EQUIVALENT"][:200]
    changed_pairs = [p for p in test_pairs if p["semantic_relation"] == "CHANGED"][:150]
    eval_pairs = equiv_pairs + changed_pairs
    eval_labels = [0] * len(equiv_pairs) + [1] * len(changed_pairs)

    print(f"  Evaluating on {len(eval_pairs)} pairs ({len(equiv_pairs)} equiv, {len(changed_pairs)} changed)")
    print(f"  {len(NOISE_LEVELS)} noise levels × {len(eval_pairs)} pairs = {len(NOISE_LEVELS) * len(eval_pairs)} scores per method")

    methods = {
        "AST": ast_fn,
        "Token": token_fn,
    }

    noise_results = {}
    for level, level_name, noise_fn in NOISE_LEVELS:
        print(f"\n  [Noise Level {level}: {level_name}]")
        noise_results[level_name] = {}

        for m_name, score_fn in methods.items():
            sims = []
            for i, p in enumerate(eval_pairs):
                if (i + 1) % 50 == 0:
                    print(f"    {m_name} {i+1}/{len(eval_pairs)}...")
                src_base_orig = load_source(p["base_path"])
                src_var_orig = load_source(p["variant_path"])

                # Apply noise to BOTH programs
                try:
                    src_base_noisy = noise_fn(src_base_orig, seed=SEED + i)
                    src_var_noisy = noise_fn(src_var_orig, seed=SEED + i + 1000)
                    s = float(score_fn(src_base_noisy, src_var_noisy))
                except Exception:
                    s = 0.5
                sims.append(s)

            eq_sims = sims[:len(equiv_pairs)]
            ch_sims = sims[len(equiv_pairs):]

            auroc = compute_auroc(sims, eval_labels)
            eq_mean = sum(eq_sims) / len(eq_sims) if eq_sims else 0.0
            ch_mean = sum(ch_sims) / len(ch_sims) if ch_sims else 0.0

            noise_results[level_name][m_name] = {
                "auroc": round(auroc, 4),
                "equiv_mean_sim": round(eq_mean, 4),
                "changed_mean_sim": round(ch_mean, 4),
                "inversion": ch_mean > eq_mean,
            }
            print(f"    {m_name}: AUROC={auroc:.4f}  EQUIV_sim={eq_mean:.4f}  CHANGED_sim={ch_mean:.4f}")

    # Compute AUROC degradation from Level 0 to higher levels
    degradation_analysis = {}
    for m_name in methods:
        baseline_auroc = noise_results["Original"][m_name]["auroc"]
        degradation_analysis[m_name] = {}
        for _, level_name, _ in NOISE_LEVELS:
            level_auroc = noise_results[level_name][m_name]["auroc"]
            degradation_analysis[m_name][level_name] = {
                "auroc": level_auroc,
                "delta_from_baseline": round(level_auroc - baseline_auroc, 4),
                "robust": abs(level_auroc - baseline_auroc) < 0.05,
            }

    # H3 verdict for robustness
    h3_robust_verdicts = {}
    for m_name in methods:
        max_degradation = max(
            abs(degradation_analysis[m_name][level_name]["delta_from_baseline"])
            for _, level_name, _ in NOISE_LEVELS
        )
        h3_robust_verdicts[m_name] = {
            "max_auroc_degradation": round(max_degradation, 4),
            "robust": max_degradation < 0.05,
            "interpretation": (
                f"Max AUROC degradation under noise = {max_degradation:.4f}. "
                f"H3 robustness {'SUPPORTED' if max_degradation < 0.05 else 'NOT_SUPPORTED'} "
                f"(threshold: Δ < 0.05)."
            ),
        }

    result = {
        "experiment": "E11",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hypothesis_addressed": ["H3"],
        "n_eval_pairs": len(eval_pairs),
        "n_equiv": len(equiv_pairs),
        "n_changed": len(changed_pairs),
        "noise_levels_tested": [n for _, n, _ in NOISE_LEVELS],
        "noise_results": noise_results,
        "degradation_analysis": degradation_analysis,
        "h3_robustness_verdicts": h3_robust_verdicts,
        "finding": (
            "Robustness test: does AUROC degrade significantly under implementation-level noise? "
            "If Δ < 0.05 across all noise levels → H3 robustness is supported. "
            "See h3_robustness_verdicts per method."
        ),
        "seed": SEED,
    }

    out_path = ARTIFACT_DIR / "results.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n=== E11 Robustness Summary ===")
    for m_name in methods:
        v = h3_robust_verdicts[m_name]
        print(f"  {m_name}: max_Δ_AUROC={v['max_auroc_degradation']:.4f}  "
              f"robust={v['robust']}  {v['interpretation']}")
    print(f"\nResults saved to: {out_path}")
    return result


if __name__ == "__main__":
    run_e11()
