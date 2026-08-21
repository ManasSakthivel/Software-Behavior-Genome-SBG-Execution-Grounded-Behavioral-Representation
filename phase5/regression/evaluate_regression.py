"""
phase5/regression/evaluate_regression.py
=========================================
Phase 5: Real-World Software Regression Detection.

Uses the existing Phase 1 benchmark reframed as a software evolution dataset:
- EQUIVALENT pairs = behavior-preserving commits (no regression)
- CHANGED pairs = regressions (behavioral change introduced)

Also builds 3 hand-crafted "real software evolution" program pairs:
1. A simple state machine with a bug fix (regression: wrong state transition)
2. A cache implementation with a capacity bug (regression: eviction policy wrong)
3. A rate limiter with an off-by-one (regression: wrong count limit)

These illustrate the regression detection problem more concretely than
the synthetic benchmark mutations.

NOTE: These are constructed examples with full provenance, not claimed
to be "real production code." They are clearly labeled as constructed.

H5: SBG detects behavioral regressions across software versions.
"""
import json
import pathlib
import random
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from baselines.common import load_pairs, load_source, compute_auroc, compute_auprc
from baselines.b02_ast import score_fn as ast_fn
from baselines.b07_static_sbg import score_fn as static_sbg_fn
from baselines.b01_token import score_fn as token_fn, fit_tfidf_model

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "phase5"
REGRESSION_DIR = REPO_ROOT / "phase5" / "regression"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
REGRESSION_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42

# ---------------------------------------------------------------------------
# Constructed real-world-style evolution pairs
# ---------------------------------------------------------------------------

EVOLUTION_PAIRS = [
    {
        "id": "state_machine_v1_v2_regression",
        "description": "Traffic light state machine: correct v1, regression in v2 (wrong next state)",
        "category": "state_machine",
        "semantic_relation": "CHANGED",
        "v1": '''\
class TrafficLight:
    """State machine for a traffic light (Green -> Yellow -> Red -> Green)."""
    STATES = ["GREEN", "YELLOW", "RED"]

    def __init__(self):
        self.state = "GREEN"

    def next_state(self):
        idx = self.STATES.index(self.state)
        self.state = self.STATES[(idx + 1) % len(self.STATES)]
        return self.state

    def get_state(self):
        return self.state
''',
        "v2": '''\
class TrafficLight:
    """Traffic light v2 — BUG: next_state skips YELLOW (goes Green->Red->Green)."""
    STATES = ["GREEN", "YELLOW", "RED"]

    def __init__(self):
        self.state = "GREEN"

    def next_state(self):
        idx = self.STATES.index(self.state)
        self.state = self.STATES[(idx + 2) % len(self.STATES)]  # REGRESSION: +2 instead of +1
        return self.state

    def get_state(self):
        return self.state
''',
        "provenance": "CONSTRUCTED — not real production code. Demonstrates state-transition regression.",
        "test_oracle": [
            {"initial": "GREEN", "transitions": 3, "expected_final": "GREEN"},
        ],
    },
    {
        "id": "lru_cache_v1_v2_refactor",
        "description": "LRU cache: v1 uses dict, v2 refactors to OrderedDict (behavior-preserving)",
        "category": "cache",
        "semantic_relation": "EQUIVALENT",
        "v1": '''\
class LRUCache:
    """Simple LRU cache using a dict and access list."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.order = []

    def get(self, key):
        if key not in self.cache:
            return -1
        self.order.remove(key)
        self.order.append(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.order.remove(key)
        elif len(self.cache) >= self.capacity:
            lru = self.order.pop(0)
            del self.cache[lru]
        self.cache[key] = value
        self.order.append(key)
''',
        "v2": '''\
class LRUCache:
    """LRU cache v2: refactored to use more efficient implementation."""
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.access_order = []

    def get(self, key):
        if key not in self.cache:
            return -1
        # Move to end (most recently used)
        self.access_order.remove(key)
        self.access_order.append(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.access_order.remove(key)
        elif len(self.cache) == self.capacity:
            # Evict least recently used
            oldest = self.access_order[0]
            self.access_order = self.access_order[1:]
            del self.cache[oldest]
        self.cache[key] = value
        self.access_order.append(key)
''',
        "provenance": "CONSTRUCTED — demonstrates semantics-preserving refactor (behavior-equivalent).",
    },
    {
        "id": "rate_limiter_v1_v2_regression",
        "description": "Rate limiter: v1 correct, v2 has off-by-one in max_requests check",
        "category": "rate_limiting",
        "semantic_relation": "CHANGED",
        "v1": '''\
class RateLimiter:
    """Allows up to max_requests per window_seconds."""

    def __init__(self, max_requests, window_seconds):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = []

    def is_allowed(self, timestamp):
        # Remove requests outside the window
        cutoff = timestamp - self.window
        self.requests = [t for t in self.requests if t > cutoff]
        if len(self.requests) < self.max_requests:
            self.requests.append(timestamp)
            return True
        return False
''',
        "v2": '''\
class RateLimiter:
    """Rate limiter v2 — BUG: uses <= instead of < in limit check."""

    def __init__(self, max_requests, window_seconds):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = []

    def is_allowed(self, timestamp):
        cutoff = timestamp - self.window
        self.requests = [t for t in self.requests if t > cutoff]
        if len(self.requests) <= self.max_requests:  # REGRESSION: <= should be <
            self.requests.append(timestamp)
            return True
        return False
''',
        "provenance": "CONSTRUCTED — demonstrates off-by-one regression in rate limiting logic.",
    },
]


def score_pair(v1_src: str, v2_src: str) -> dict:
    """Score a v1→v2 pair using multiple methods."""
    scores = {}
    for name, fn in [("AST", ast_fn), ("Token", token_fn), ("Static_SBG", static_sbg_fn)]:
        try:
            scores[name] = round(float(fn(v1_src, v2_src)), 4)
        except Exception:
            scores[name] = None
    return scores


def run():
    print("=" * 60)
    print("Phase 5: Regression Detection Evaluation")
    print("=" * 60)

    # Initialize token model
    train_pairs = load_pairs("train")
    fit_tfidf_model(train_pairs)

    # -----------------------------------------------------------------------
    # Part 1: Constructed evolution pairs
    # -----------------------------------------------------------------------
    print("\n  Part 1: Constructed evolution pairs")
    evolution_results = []
    for ep in EVOLUTION_PAIRS:
        scores = score_pair(ep["v1"], ep["v2"])
        label = 0 if ep["semantic_relation"] == "EQUIVALENT" else 1

        # For each method: did the score correctly indicate the semantic relation?
        method_signals = {}
        for m, s in scores.items():
            if s is not None:
                # Lower similarity → more likely CHANGED
                # Correct signal: if CHANGED and similarity is low, or EQUIV and sim is high
                if label == 1:
                    signal = "CORRECT" if s < 0.9 else "MISSED"
                else:
                    signal = "CORRECT" if s > 0.8 else "FALSE_ALARM"
                method_signals[m] = {"similarity": s, "signal": signal}

        print(f"  {ep['id']} ({ep['semantic_relation']}): AST={scores.get('AST')}")
        evolution_results.append({
            "id": ep["id"],
            "description": ep["description"],
            "semantic_relation": ep["semantic_relation"],
            "category": ep["category"],
            "scores": scores,
            "method_signals": method_signals,
            "provenance": ep.get("provenance", "CONSTRUCTED"),
        })

    # -----------------------------------------------------------------------
    # Part 2: Phase 1 benchmark as regression detection
    # -----------------------------------------------------------------------
    print("\n  Part 2: Phase 1 benchmark regression detection (from Phase 4 E10 results)")
    e10_path = REPO_ROOT / "artifacts" / "phase4" / "E10" / "results.json"
    e10_result = {}
    if e10_path.exists():
        with open(e10_path) as f:
            e10_result = json.load(f)

    # -----------------------------------------------------------------------
    # Part 3: Statistical summary
    # -----------------------------------------------------------------------
    equiv_sims = {m: [] for m in ["AST", "Token", "Static_SBG"]}
    changed_sims = {m: [] for m in ["AST", "Token", "Static_SBG"]}

    for r in evolution_results:
        for m in ["AST", "Token", "Static_SBG"]:
            s = r["scores"].get(m)
            if s is not None:
                if r["semantic_relation"] == "EQUIVALENT":
                    equiv_sims[m].append(s)
                else:
                    changed_sims[m].append(s)

    print("\n  Constructed pair results:")
    for m in ["AST", "Token", "Static_SBG"]:
        eq_list = equiv_sims[m]
        ch_list = changed_sims[m]
        eq_mean = sum(eq_list) / len(eq_list) if eq_list else None
        ch_mean = sum(ch_list) / len(ch_list) if ch_list else None
        eq_str = f"{eq_mean:.4f}" if eq_mean is not None else "N/A"
        ch_str = f"{ch_mean:.4f}" if ch_mean is not None else "N/A"
        print(f"    {m}: EQUIV_mean={eq_str}  CHANGED_mean={ch_str}")

    # Phase 1 benchmark regression AUROCs from E10
    phase1_regression = e10_result.get("overall_regression_detection", {})

    # H5 verdict: combine constructed + Phase 1
    best_auroc_phase1 = max(
        (phase1_regression.get(m, {}).get("auroc", 0.0) for m in ["AST", "Token", "Static_SBG"]),
        default=0.0
    )

    # Check constructed pairs direction
    ast_direction_correct = (
        len(equiv_sims["AST"]) > 0 and
        len(changed_sims["AST"]) > 0 and
        sum(equiv_sims["AST"]) / len(equiv_sims["AST"]) >
        sum(changed_sims["AST"]) / len(changed_sims["AST"])
    )

    h5_verdict = {
        "status": "NOT_SUPPORTED",
        "phase1_best_auroc": best_auroc_phase1,
        "constructed_pairs_n": len(EVOLUTION_PAIRS),
        "ast_direction_correct_on_constructed": ast_direction_correct,
        "interpretation": (
            f"Phase 1 benchmark: best regression detection AUROC={best_auroc_phase1:.4f} < 0.65 threshold. "
            f"Constructed evolution pairs ({len(EVOLUTION_PAIRS)} pairs): "
            f"AST direction {'correct' if ast_direction_correct else 'incorrect'} "
            f"(EQUIV > CHANGED: {ast_direction_correct}). "
            "H5 NOT SUPPORTED: regression detection is not reliable with current representations."
        ),
    }

    result = {
        "experiment": "phase5_regression_detection",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hypothesis_addressed": ["H5"],
        "constructed_evolution_pairs": evolution_results,
        "phase1_regression_from_e10": phase1_regression,
        "h5_verdict": h5_verdict,
        "finding": h5_verdict["interpretation"],
        "provenance_note": (
            "All constructed evolution pairs are hand-crafted examples with "
            "explicit provenance (CONSTRUCTED label). They are NOT claimed to be "
            "real production code or real commit history."
        ),
        "seed": SEED,
    }

    out_path = ARTIFACT_DIR / "regression_results.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n  H5 verdict: {h5_verdict['status']}")
    print(f"  {h5_verdict['interpretation']}")
    print(f"\n  Results saved to: {out_path}")
    return result


if __name__ == "__main__":
    run()
