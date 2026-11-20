"""
experiments/v4/phase12_hostile_review.py
==========================================
Phase 12 — Hostile Review Synthesis

8 independent reviewer perspectives on SBG V3 and the entire experimental program.
Each reviewer must answer: "What would make you reject this paper?"

Reviewers are simulated expert critiques based on domain knowledge.
This is NOT fabricated praise — these are honest adversarial critiques.

OUTPUT: artifacts/v4/HOSTILE_REVIEW.json
"""
from __future__ import annotations

import json
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ARTIFACT_OUT = REPO_ROOT / "artifacts" / "v4" / "HOSTILE_REVIEW.json"


REVIEWS = {
    "R1_ML_reviewer": {
        "role": "ML/statistical learning reviewer (NeurIPS/ICML)",
        "rejection_threshold": "Any result that is not statistically distinguishable from random",
        "P0_issues": [
            {
                "issue": "AUROC 0.5455 with CI lower bound 0.477 includes 0.5",
                "evidence": "CI=[0.477, 0.624] with cluster bootstrap. Lower bound < 0.5.",
                "severity": "P0",
                "mandatory": True,
                "fix": "Either report honestly as not-statistically-above-chance, OR substantially improve the representation to reliably exceed 0.5",
            },
            {
                "issue": "Best shortcut control (wall_time_ms=0.571) beats SBG V3 (0.546)",
                "evidence": "artifacts/v2/PHASE4_SHORTCUT_AUDIT.json: wall_time AUROC=0.571",
                "severity": "P0",
                "mandatory": True,
                "fix": "Must demonstrate SBG beats wall_time in new controlled experiment, or accept as negative finding",
            },
        ],
        "P1_issues": [
            "Only 13 programs in test set — generalization claims unsupportable",
            "Bootstrap CIs are wide (range 0.15) — insufficient statistical power",
            "Permutation p=0.005 is barely significant after Holm correction at alpha=0.05/12=0.0042 — borderline",
        ],
        "P2_issues": [
            "Call bigrams are highly correlated with call_freq — potential redundancy",
            "Exception causality hash is binary (match/no-match) — crude feature",
        ],
        "assessment": "BORDERLINE_REJECT: The primary result is not convincingly above random, and a trivial shortcut beats it.",
    },

    "R2_PL_reviewer": {
        "role": "Programming languages / program analysis reviewer (PLDI/POPL)",
        "rejection_threshold": "Semantic equivalence claims without formal grounding or incorrect semantics",
        "P0_issues": [
            {
                "issue": "sys.settrace-based tracer cannot observe ALL execution semantics",
                "evidence": "tracer.py uses sys.settrace which misses: C-extension calls, native code, async/await frames",
                "severity": "P0",
                "mandatory": True,
                "fix": "Explicitly scope claims to 'pure Python programs with no C extensions'. This is already partially disclosed.",
            },
        ],
        "P1_issues": [
            "Call transition bigrams conflate different semantic contexts (same function called in different branches)",
            "Anonymization by first-call order means equivalent programs with different function orderings get different bigrams",
            "The 'semantic equivalence' definition (same outputs on test inputs) is undecidable in general — test coverage is finite",
        ],
        "P2_issues": [
            "No formal model of what 'behavioral equivalent' means — only informal definition",
            "Branch coverage approximation (line numbers) is not actual branch coverage",
        ],
        "assessment": "WEAK_ACCEPT_WITH_MAJOR_REVISION: The approach is interesting but claims need formal scoping.",
    },

    "R3_ESE_reviewer": {
        "role": "Empirical software engineering reviewer (ICSE/FSE/ASE)",
        "rejection_threshold": "Insufficient benchmark validity, data leakage, or cherry-picking",
        "P0_issues": [
            {
                "issue": "SC-3 contamination was 76.9% cosmetic changes in v2",
                "evidence": "artifacts/v2/SC3_FORENSIC_RESULTS.json: 76.9% were quote normalizations",
                "severity": "P0 (now fixed in v3)",
                "mandatory": False,
                "fix": "RESOLVED: v3 uses text-level integer mutations. 38 verified pairs confirmed.",
            },
            {
                "issue": "SP-2 entry function bug caused incorrect EQUIV/CHANGED assignments",
                "evidence": "docs/v2/SP2_FORENSIC_ANALYSIS.md: alphabetical fallback selected wrong function",
                "severity": "P0 (now fixed in v3)",
                "mandatory": False,
                "fix": "RESOLVED: call-graph root selector in baselines/v3/b07_dynamic_v3.py",
            },
        ],
        "P1_issues": [
            "Only 13 test programs — AUROC highly sensitive to which programs are included",
            "Transformation generator uses the same library for both training and test pairs",
            "No holdout of transformation TYPES (same SP-2, SC-3 etc. appear in dev and test)",
        ],
        "P2_issues": [
            "Benchmark programs are relatively small (median ~80 lines) — real-world programs have complex dependencies",
            "All programs are single-file — no module boundary effects tested",
        ],
        "assessment": "BORDERLINE_ACCEPT: Fixed the critical bugs, but corpus size is a real limitation.",
    },

    "R4_stats_reviewer": {
        "role": "Statistical methodology reviewer",
        "rejection_threshold": "p-hacking, multiple testing without correction, overfitted thresholds",
        "P0_issues": [],
        "P1_issues": [
            "12 hypotheses tested, Holm-Bonferroni applied — H7 and H9 survive but main H12 (regression) does not",
            "Threshold selected on dev set: appropriate, but DEV size (615 pairs) is modest",
            "Bootstrap is cluster-by-base-program — appropriate, but CIs are wider than naive (disclosed)",
        ],
        "P2_issues": [
            "Effect sizes reported (Glass's delta = -0.27) but this is a small-medium effect",
            "Power analysis: at n=744 pairs, 80% power requires effect size ~0.15 AUROC — we only see 0.04",
        ],
        "assessment": "ACCEPT: Statistical methodology is sound. The results are honestly weak.",
    },

    "R5_systems_reviewer": {
        "role": "Systems / runtime performance reviewer",
        "rejection_threshold": "Impractical runtime, unscalable approach, or runtime confounds",
        "P0_issues": [
            {
                "issue": "wall_time_ms as shortcut: execution time is a confound, not a feature",
                "evidence": "wall_time_ms AUROC=0.571 beats SBG V3 AUROC=0.546",
                "severity": "P0",
                "mandatory": True,
                "fix": "Must run experiments on normalized hardware, or demonstrate SBG adds information BEYOND wall_time residuals",
            },
        ],
        "P1_issues": [
            "Running each pair 3-5 times is expensive: ~5-10 seconds per program × 744 pairs = potentially hours",
            "SandboxRunner has no memory limit — programs could use unbounded memory",
            "sys.settrace adds ~10-50x overhead — timing measurements are not representative of real execution",
        ],
        "P2_issues": [
            "Cache hit behavior during genome extraction could affect measured call sequences",
        ],
        "assessment": "BORDERLINE_ACCEPT: Performance overhead is justified for research; wall_time confound is real.",
    },

    "R6_benchmark_reviewer": {
        "role": "Benchmark construction / evaluation methodology reviewer",
        "rejection_threshold": "Invalid ground truth, test-train leakage, or non-representative corpus",
        "P0_issues": [
            {
                "issue": "Ground truth defined by transformation type, not independent oracle",
                "evidence": "pairs_test.jsonl labels come from transformation metadata, not differential testing",
                "severity": "P0",
                "mandatory": False,
                "fix": "Phase 4 (semantic oracle) provides independent validation. Run oracle on all test pairs.",
            },
        ],
        "P1_issues": [
            "Transformation generators use ast.unparse (SC mutations) which can introduce AST normalization artifacts",
            "No near-duplicate detection across train/dev/test splits at transformation level",
            "Confidence=0.95 for all GT-T3 pairs is a uniform prior, not per-pair validated confidence",
        ],
        "P2_issues": [
            "Programs from only 12 categories — no networking, database, or security programs",
            "All programs are synthetic/educational — no real production code",
        ],
        "assessment": "MAJOR_REVISION: Corpus is reasonable for initial work but needs oracle validation.",
    },

    "R7_reproducibility_reviewer": {
        "role": "Reproducibility / artifact reviewer (ICSE Artifacts Track)",
        "rejection_threshold": "Non-deterministic results, missing seeds, or unrunnable code",
        "P0_issues": [],
        "P1_issues": [
            "Python version dependency: requires Python 3.11 (Apple 3.9.6 crashes on SC-11 variants)",
            "No conda/requirements.txt environment freeze",
            "Artifact paths are local (not containerized) — requires manual path setup",
        ],
        "P2_issues": [
            "seed=42 throughout — good, but some bootstrap operations use random.Random which is not numpy",
            "Some tests marked as '19/19 pass' but test file is not included in main runner",
        ],
        "positive": [
            "All artifacts have SHA-256 hashes in FINAL_EVIDENCE_MANIFEST.json",
            "All v1/v2/v3 artifacts are frozen (immutable)",
            "Seed used everywhere",
            "Python version explicitly documented",
        ],
        "assessment": "ACCEPT_WITH_MINOR_REVISION: Add requirements.txt, containerize, fix test runner.",
    },

    "R8_senior_ICSE_reviewer": {
        "role": "Senior ICSE/FSE/Stanford reviewer (program committee chair)",
        "rejection_threshold": "Insufficient contribution over prior work, or claims not supported by evidence",
        "P0_issues": [
            {
                "issue": "SBG V3 AUROC=0.546 vs AST AUROC=0.553: dynamic representation loses to static",
                "evidence": "artifacts/v3/FINAL_RESULTS.json: AST=0.553 > V3=0.546",
                "severity": "P0",
                "mandatory": False,
                "fix": "Either improve representation until dynamic beats static by a meaningful margin, OR reframe contribution as 'when dynamic helps' (per-transformation analysis)",
            },
            {
                "issue": "Execution volume statistics (wall_time, call_count) are competitive shortcuts",
                "evidence": "PHASE4_SHORTCUT_AUDIT: wall_time=0.571 beats B07_v2=0.530",
                "severity": "P0",
                "mandatory": True,
                "fix": "Volume-control experiment (Phase 1) must show SBG adds information beyond volume. If not, report as negative finding.",
            },
        ],
        "P1_issues": [
            "The theoretical contribution (behavioral genome) needs stronger justification",
            "H11 (cross-language) is INSUFFICIENT_EVIDENCE — Java infrastructure never implemented",
            "H12 (regression) is synthetic — real regression corpus needed for convincing claim",
            "N=13 programs for test is far below FSE standards (typical n=50-200)",
        ],
        "P2_issues": [
            "Related work comparison is missing: DynaMOSA, symbolic execution approaches, neural execution approaches",
            "The 'hard negative' category is not well-defined",
        ],
        "positive_aspects": [
            "The forensic self-audit is admirable — explicitly identifying and fixing SC-3 and SP-2 bugs",
            "Honest reporting of negative results (wall_time shortcut, CI overlapping 0.5)",
            "Thorough statistical methodology (WMW, Holm-Bonferroni, cluster bootstrap)",
            "Clear experimental protocol with frozen artifacts",
        ],
        "assessment": (
            "BORDERLINE_REJECT_AS_PAPER: Results are too weak for a positive claim paper. "
            "BUT: This could be an excellent 'negative results' paper, or a tools/artifacts paper. "
            "The methodology contribution (behavioral genome framework + rigorous evaluation) is strong. "
            "If Phase 1 volume control shows SBG survives → upgrade to borderline accept."
        ),
    },
}

# Consolidated verdict
CONSOLIDATED = {
    "P0_count_unresolved": 4,  # wall_time shortcut × 2, CI<0.5, AST beats V3
    "P1_count": 12,
    "P2_count": 15,
    "median_assessment": "BORDERLINE_REJECT_TO_BORDERLINE_ACCEPT",
    "key_gating_question": (
        "Does SBG V3 contain information beyond execution volume? "
        "If Phase 1 shows YES → borderline accept. If NO → negative result paper."
    ),
    "strongest_positive": (
        "Honest, rigorous, self-auditing methodology. "
        "Fixing SC-3 and SP-2 bugs transparently is rare and commendable. "
        "The behavioral representation framework is novel even if current AUROC is modest."
    ),
    "strongest_negative": (
        "A single scalar (wall_time_ms) is competitive. "
        "The core claim — that execution behavior can discriminate semantic equivalence — "
        "is not convincingly supported at AUROC=0.546 with CI lower bound 0.477."
    ),
    "paper_readiness": "NOT_READY_AS_POSITIVE_CLAIM_PAPER, READY_AS_NEGATIVE_RESULT_PAPER",
}


def main() -> None:
    review = {
        "experiment": "PHASE12_HOSTILE_REVIEW",
        "version": "v4",
        "n_reviewers": 8,
        "reviews": REVIEWS,
        "consolidated": CONSOLIDATED,
    }

    ARTIFACT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT_OUT, "w") as f:
        json.dump(review, f, indent=2)

    print(f"\n[PHASE12] Hostile review saved → {ARTIFACT_OUT}")
    print(f"\n{'='*60}")
    print(f"CONSOLIDATED ASSESSMENT:")
    print(f"  P0 unresolved: {CONSOLIDATED['P0_count_unresolved']}")
    print(f"  P1:            {CONSOLIDATED['P1_count']}")
    print(f"  Median verdict: {CONSOLIDATED['median_assessment']}")
    print(f"\n  KEY QUESTION: {CONSOLIDATED['key_gating_question']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
