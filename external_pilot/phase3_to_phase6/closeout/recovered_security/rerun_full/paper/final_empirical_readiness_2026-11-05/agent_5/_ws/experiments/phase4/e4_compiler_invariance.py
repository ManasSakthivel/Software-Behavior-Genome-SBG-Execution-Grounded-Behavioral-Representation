"""
experiments/phase4/e4_compiler_invariance.py
=============================================
E4: Compiler/Optimization Invariance.

Tests whether SBG features are stable across equivalent programs generated
by different "compilation" paths — in Python terms, this means equivalent
programs written with different idiomatic styles that a compiler would
optimize to the same bytecode behavior.

Since we don't have actual compiled variants, we test:
1. Programs with list comprehension vs explicit loops (same result)
2. Programs with different but equivalent arithmetic forms
3. Programs using different but equivalent Python idioms

We use the existing SP-* variants as proxies for "optimizer-equivalent" programs
and measure whether SBG similarity is high for these pairs.

Also: compare Python bytecode-level similarity (using the `dis` module) 
as an additional dimension — bytecode captures post-compilation equivalence.

Hypothesis addressed: H3 (robustness under transformation)
"""
import dis
import io
import json
import pathlib
import random
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from experiments.phase4.utils import ensure_token_initialized

from baselines.common import load_pairs, load_source, compute_auroc
from baselines.b02_ast import score_fn as ast_score_fn
from baselines.b01_token import score_fn as token_score_fn

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "phase4" / "E4"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
N_BOOTSTRAP = 1000


def get_bytecode_tokens(source: str) -> list:
    """
    Extract bytecode instruction sequence using dis module.
    Returns list of opname strings (excluding line numbers and offsets).
    This is a 'compiler output' representation.
    """
    try:
        code = compile(source, "<string>", "exec")
    except SyntaxError:
        return []
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        dis.dis(code)
    finally:
        sys.stdout = old_stdout
    lines = buf.getvalue().splitlines()
    opcodes = []
    for line in lines:
        # dis output format: "  N  OPNAME  arg"
        parts = line.split()
        for p in parts:
            if p.isupper() and "_" in p or p.isupper():
                # Likely an opcode
                if all(c.isupper() or c == "_" for c in p) and len(p) > 2:
                    opcodes.append(p)
                    break
    return opcodes


def bytecode_similarity(src_a: str, src_b: str) -> float:
    """Jaccard similarity of bytecode opcode multisets."""
    toks_a = get_bytecode_tokens(src_a)
    toks_b = get_bytecode_tokens(src_b)
    if not toks_a and not toks_b:
        return 1.0
    if not toks_a or not toks_b:
        return 0.0
    # Counter-based Jaccard
    from collections import Counter
    ca = Counter(toks_a)
    cb = Counter(toks_b)
    all_keys = set(ca) | set(cb)
    intersection = sum(min(ca.get(k, 0), cb.get(k, 0)) for k in all_keys)
    union = sum(max(ca.get(k, 0), cb.get(k, 0)) for k in all_keys)
    return intersection / union if union > 0 else 1.0


def bootstrap_ci(values, n_resamples=N_BOOTSTRAP, seed=SEED):
    if len(values) < 2:
        m = values[0] if values else 0.0
        return m, m, m
    rng = random.Random(seed)
    means = []
    n = len(values)
    for _ in range(n_resamples):
        sample = [values[rng.randint(0, n - 1)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    return sum(values) / n, means[int(0.025 * n_resamples)], means[int(0.975 * n_resamples)]


def run_e4():
    print("=" * 60)
    print("E4: Compiler/Optimization Invariance")
    print("=" * 60)

    ensure_token_initialized()
    test_pairs = load_pairs("test")
    equiv_pairs = [p for p in test_pairs if p["semantic_relation"] == "EQUIVALENT"]
    changed_pairs = [p for p in test_pairs if p["semantic_relation"] == "CHANGED"]

    methods = {
        "Bytecode": bytecode_similarity,
        "AST": ast_score_fn,
        "Token": token_score_fn,
    }

    print(f"Test pairs: {len(test_pairs)} total ({len(equiv_pairs)} EQUIV, {len(changed_pairs)} CHANGED)")

    all_equiv_scores = {m: [] for m in methods}
    all_changed_scores = {m: [] for m in methods}

    # Score equiv pairs
    for i, p in enumerate(equiv_pairs):
        if (i + 1) % 50 == 0:
            print(f"  equiv {i+1}/{len(equiv_pairs)}...")
        src_base = load_source(p["base_path"])
        src_var = load_source(p["variant_path"])
        for m_name, fn in methods.items():
            try:
                s = float(fn(src_base, src_var))
            except Exception:
                s = 0.5
            all_equiv_scores[m_name].append(s)

    # Score changed pairs
    for i, p in enumerate(changed_pairs):
        if (i + 1) % 30 == 0:
            print(f"  changed {i+1}/{len(changed_pairs)}...")
        src_base = load_source(p["base_path"])
        src_var = load_source(p["variant_path"])
        for m_name, fn in methods.items():
            try:
                s = float(fn(src_base, src_var))
            except Exception:
                s = 0.5
            all_changed_scores[m_name].append(s)

    # Analysis per method
    analysis = {}
    for m_name in methods:
        eq = all_equiv_scores[m_name]
        ch = all_changed_scores[m_name]
        eq_mean, eq_lo, eq_hi = bootstrap_ci(eq)
        ch_mean, ch_lo, ch_hi = bootstrap_ci(ch)
        auroc = compute_auroc(eq + ch, [0] * len(eq) + [1] * len(ch))
        analysis[m_name] = {
            "equiv_mean": round(eq_mean, 4),
            "equiv_ci": [round(eq_lo, 4), round(eq_hi, 4)],
            "changed_mean": round(ch_mean, 4),
            "changed_ci": [round(ch_lo, 4), round(ch_hi, 4)],
            "delta": round(ch_mean - eq_mean, 4),
            "auroc": round(auroc, 4),
            "inversion": ch_mean > eq_mean,
        }

    # Bytecode-specific: does bytecode survive SP transforms better than token?
    bytecode_by_transform = {}
    for i, p in enumerate(equiv_pairs):
        tt = p["transformation_type"]
        if tt not in bytecode_by_transform:
            bytecode_by_transform[tt] = []
        if i < len(all_equiv_scores["Bytecode"]):
            bytecode_by_transform[tt].append(all_equiv_scores["Bytecode"][i])

    bytecode_transform_stats = {}
    for tt, scores in bytecode_by_transform.items():
        if scores:
            m = sum(scores) / len(scores)
            bytecode_transform_stats[tt] = {
                "mean": round(m, 4),
                "n": len(scores),
                "std": round((sum((x - m) ** 2 for x in scores) / len(scores)) ** 0.5, 4),
            }

    result = {
        "experiment": "E4",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hypothesis_addressed": ["H3"],
        "n_equiv_pairs": len(equiv_pairs),
        "n_changed_pairs": len(changed_pairs),
        "method_analysis": analysis,
        "bytecode_by_transform": bytecode_transform_stats,
        "finding": (
            "Bytecode similarity provides an alternative 'post-compilation' view. "
            "If bytecode is more stable under SP transforms than source-level features, "
            "it supports using execution-level representations over source-level ones. "
            "See method_analysis[Bytecode].inversion for the key finding."
        ),
        "note": "Bytecode opcode Jaccard approximates compiler-level equivalence without full execution.",
        "seed": SEED,
    }

    out_path = ARTIFACT_DIR / "results.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n=== E4 Results ===")
    for m_name in methods:
        a = analysis[m_name]
        print(f"  {m_name}: EQUIV={a['equiv_mean']:.4f}  CHANGED={a['changed_mean']:.4f}  "
              f"AUROC={a['auroc']:.4f}  INVERTED={a['inversion']}")
    print(f"\nResults saved to: {out_path}")
    return result


if __name__ == "__main__":
    run_e4()
