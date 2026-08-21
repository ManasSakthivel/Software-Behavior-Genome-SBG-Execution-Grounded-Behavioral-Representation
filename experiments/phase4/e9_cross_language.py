"""
experiments/phase4/e9_cross_language.py
=========================================
E9: Cross-Language Equivalence — Preliminary.

Phase 5 will build a full cross-language benchmark. This experiment establishes:
1. The difficulty of cross-language detection with current representations
2. Which features survive language boundaries (control structure) vs. don't (tokens)
3. A small set of illustrative cross-language pairs (NOT included in quantitative claims)

The illustrative pairs are Python programs from the benchmark compared to
structurally equivalent programs written in a different Python idiom that
approaches a different-language style (e.g., explicit index-based loops = C-style,
list comprehensions = Haskell-style map). This is NOT true cross-language,
but characterizes what features degrade.

Hypothesis addressed: H4 (language-agnostic — preliminary assessment only)
"""
import json
import pathlib
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from experiments.phase4.utils import ensure_token_initialized

from baselines.b02_ast import score_fn as ast_fn, ast_sequence_similarity, ast_node_type_similarity
from baselines.b01_token import score_fn as token_fn

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "phase4" / "E9"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Illustrative cross-language style pairs
# Each pair: (python_style_A, different_language_style_B, description)
# These use different idiomatic styles to approximate cross-language divergence
# ---------------------------------------------------------------------------

ILLUSTRATIVE_PAIRS = [
    {
        "id": "bubble_sort_python_vs_c_style",
        "description": "Bubble sort: Python idiomatic vs C-style index loops",
        "label": "EQUIVALENT",
        "src_a": """\
def bubble_sort(arr):
    n = len(arr)
    for i in range(n - 1):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
""",
        "src_b": """\
def bubble_sort(arr):
    # C-style: explicit length, index-based swap with temp variable
    n = len(arr)
    i = 0
    while i < n - 1:
        j = 0
        while j < n - 1 - i:
            if arr[j] > arr[j + 1]:
                temp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = temp
            j = j + 1
        i = i + 1
    return arr
""",
    },
    {
        "id": "fibonacci_recursive_vs_iterative",
        "description": "Fibonacci: Python recursive vs iterative (different structure, same output)",
        "label": "DIFFERENT_STRUCTURE_SAME_BEHAVIOR",
        "src_a": """\
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)
""",
        "src_b": """\
def fib(n):
    # JavaScript-style: iterative with explicit variables
    if n <= 1:
        return n
    a = 0
    b = 1
    i = 2
    while i <= n:
        c = a + b
        a = b
        b = c
        i = i + 1
    return b
""",
    },
    {
        "id": "linear_search_python_vs_functional",
        "description": "Linear search: explicit loop vs functional style",
        "label": "EQUIVALENT",
        "src_a": """\
def linear_search(arr, target):
    for i, val in enumerate(arr):
        if val == target:
            return i
    return -1
""",
        "src_b": """\
def linear_search(arr, target):
    # Haskell-style: using next() with generator (functional)
    result = next((i for i, val in enumerate(arr) if val == target), -1)
    return result
""",
    },
    {
        "id": "sum_list_python_vs_c_style",
        "description": "Sum of list: Pythonic sum() vs explicit C-style accumulator",
        "label": "EQUIVALENT",
        "src_a": """\
def sum_list(numbers):
    return sum(numbers)
""",
        "src_b": """\
def sum_list(numbers):
    # C-style accumulator
    total = 0
    i = 0
    while i < len(numbers):
        total = total + numbers[i]
        i = i + 1
    return total
""",
    },
    {
        "id": "max_element_python_vs_java_style",
        "description": "Find max element: Python max() vs Java-style for loop with comparison",
        "label": "EQUIVALENT",
        "src_a": """\
def find_max(arr):
    if not arr:
        return None
    return max(arr)
""",
        "src_b": """\
def find_max(arr):
    # Java-style: explicit tracking variable
    if arr is None or len(arr) == 0:
        return None
    maximum = arr[0]
    for i in range(1, len(arr)):
        if arr[i] > maximum:
            maximum = arr[i]
    return maximum
""",
    },
]


def analyze_pair(pair: dict) -> dict:
    src_a = pair["src_a"]
    src_b = pair["src_b"]
    scores = {
        "token_tfidf": token_fn(src_a, src_b),
        "ast_sequence": ast_sequence_similarity(src_a, src_b),
        "ast_node_type": ast_node_type_similarity(src_a, src_b),
    }
    return {
        "id": pair["id"],
        "description": pair["description"],
        "label": pair["label"],
        "scores": {k: round(v, 4) for k, v in scores.items()},
        "token_degradation": round(1.0 - scores["token_tfidf"], 4),
        "ast_seq_degradation": round(1.0 - scores["ast_sequence"], 4),
        "ast_type_degradation": round(1.0 - scores["ast_node_type"], 4),
    }


def run_e9():
    print("=" * 60)
    print("E9: Cross-Language Equivalence (Preliminary)")
    print("=" * 60)

    ensure_token_initialized()
    pair_results = []
    for pair in ILLUSTRATIVE_PAIRS:
        res = analyze_pair(pair)
        pair_results.append(res)
        print(f"  {res['id']}:")
        print(f"    Token={res['scores']['token_tfidf']:.4f}  "
              f"AST_seq={res['scores']['ast_sequence']:.4f}  "
              f"AST_type={res['scores']['ast_node_type']:.4f}")

    # Average degradation across pairs
    avg_token = sum(r["scores"]["token_tfidf"] for r in pair_results) / len(pair_results)
    avg_ast_seq = sum(r["scores"]["ast_sequence"] for r in pair_results) / len(pair_results)
    avg_ast_type = sum(r["scores"]["ast_node_type"] for r in pair_results) / len(pair_results)

    print(f"\n  Average similarities across {len(pair_results)} illustrative pairs:")
    print(f"    Token:    {avg_token:.4f}")
    print(f"    AST_seq:  {avg_ast_seq:.4f}")
    print(f"    AST_type: {avg_ast_type:.4f}")

    result = {
        "experiment": "E9",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hypothesis_addressed": ["H4"],
        "status": "PRELIMINARY_ONLY",
        "warning": (
            "Full cross-language evaluation deferred to Phase 5. "
            "These pairs are Python-only with different idiomatic styles. "
            "They approximate cross-language divergence but are NOT true cross-language pairs. "
            "Do NOT include these results in quantitative claims."
        ),
        "n_illustrative_pairs": len(ILLUSTRATIVE_PAIRS),
        "pair_results": pair_results,
        "aggregate_similarities": {
            "token_mean": round(avg_token, 4),
            "ast_sequence_mean": round(avg_ast_seq, 4),
            "ast_node_type_mean": round(avg_ast_type, 4),
        },
        "features_that_survive_language_boundary": [
            "AST node type distribution (control flow patterns remain)",
            "High-level algorithm structure (loops, conditionals)",
            "Cyclomatic complexity approximation",
            "Call graph topology (same functions called in same order)",
        ],
        "features_that_fail_cross_language": [
            "Token/TF-IDF (language syntax tokens differ completely)",
            "Variable/function name normalization (works for same language)",
            "AST sequence edit distance (different syntax trees)",
            "Keyword frequency (def/function/fn differ by language)",
        ],
        "h4_status": (
            "NOT_EVALUABLE — insufficient cross-language data in Phase 4. "
            "Full H4 evaluation requires Phase 5 Python↔Java or Python↔JavaScript benchmark."
        ),
        "phase5_requirement": (
            "Phase 5 must build at least 50 program pairs where the same specification "
            "is implemented in Python and Java/JavaScript. Only then can H4 be evaluated."
        ),
    }

    out_path = ARTIFACT_DIR / "results.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n  H4 status: {result['h4_status']}")
    print(f"\nResults saved to: {out_path}")
    return result


if __name__ == "__main__":
    run_e9()
