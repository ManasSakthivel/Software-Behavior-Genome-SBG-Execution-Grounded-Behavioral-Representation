"""
baselines/common.py — Shared utilities for SBG Phase 3 baselines.

Convention:
  score = similarity(base, variant) in [0, 1]
  HIGH score → EQUIVALENT (label=0)
  LOW score  → CHANGED   (label=1)

Classification rule:
  predicted = CHANGED  if score < threshold
  predicted = EQUIV    if score >= threshold

For AUROC: we compute ROC for the CHANGED class.
  - positive class = CHANGED (label=1)
  - score used = 1 - similarity  (distance → higher = more likely CHANGED)
"""
import json
import math
import pathlib
import random

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PAIRS_DIR = REPO_ROOT / "benchmark" / "datasets"
ARTIFACTS_DIR = REPO_ROOT / "artifacts" / "phase3"

EQUIV_LABEL = "EQUIVALENT"   # label=0
CHANGED_LABEL = "CHANGED"    # label=1 (positive class)


def load_pairs(split: str) -> list:
    path = PAIRS_DIR / f"pairs_{split}.jsonl"
    pairs = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))
    return pairs


def load_source(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _trapz(xs, ys):
    """Trapezoidal integration."""
    area = 0.0
    for i in range(len(xs) - 1):
        area += (xs[i + 1] - xs[i]) * (ys[i] + ys[i + 1]) / 2.0
    return area


def compute_auroc(similarities: list, labels: list) -> float:
    """
    Compute AUROC for CHANGED detection.
    similarities[i] = similarity score (high = EQUIVALENT)
    labels[i] = 0 (EQUIVALENT) or 1 (CHANGED)
    We use distance = 1 - similarity as the score for CHANGED class.
    """
    # Convert to (distance, label) and sort descending by distance
    n = len(similarities)
    if n == 0:
        return 0.5
    pairs = sorted(zip(similarities, labels), key=lambda x: x[0])  # ascending sim = descending dist
    # Compute ROC: sweep threshold from low to high similarity
    # Positive class = CHANGED (label=1)
    n_pos = sum(1 for l in labels if l == 1)
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    tprs, fprs = [0.0], [0.0]
    tp = fp = 0
    # Thresholds: predict CHANGED (positive) if sim < threshold
    # Sort from low sim to high sim; lower threshold = more predictions of CHANGED
    for sim, lbl in pairs:  # ascending similarity = predict all as CHANGED first
        if lbl == 1:
            tp += 1
        else:
            fp += 1
        tprs.append(tp / n_pos)
        fprs.append(fp / n_neg)
    tprs.append(1.0)
    fprs.append(1.0)
    return _trapz(fprs, tprs)


def compute_auprc(similarities: list, labels: list) -> float:
    """Average precision for CHANGED detection."""
    n = len(similarities)
    if n == 0:
        return 0.5
    n_pos = sum(1 for l in labels if l == 1)
    if n_pos == 0:
        return 0.5
    # Sort ascending by similarity (descending by distance = score for CHANGED)
    ranked = sorted(zip(similarities, labels), key=lambda x: x[0])
    precisions, recalls = [1.0], [0.0]
    tp = fp = 0
    for sim, lbl in ranked:
        if lbl == 1:
            tp += 1
        else:
            fp += 1
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / n_pos
        precisions.append(prec)
        recalls.append(rec)
    return _trapz(recalls, precisions)


def find_optimal_threshold(similarities: list, labels: list) -> float:
    """
    Find threshold on SIMILARITY that maximises F1 for CHANGED detection.
    Rule: predict CHANGED if similarity < threshold.
    """
    if not similarities:
        return 0.5
    unique = sorted(set(similarities))
    # Add sentinel thresholds
    if unique[0] > 0.0:
        unique = [0.0] + unique
    unique.append(unique[-1] + 1e-6)

    best_f1 = -1.0
    best_t = 0.5
    for t in unique:
        tp = fp = fn = tn = 0
        for sim, lbl in zip(similarities, labels):
            pred = 1 if sim < t else 0  # CHANGED if below threshold
            if lbl == 1 and pred == 1:
                tp += 1
            elif lbl == 0 and pred == 1:
                fp += 1
            elif lbl == 1 and pred == 0:
                fn += 1
            else:
                tn += 1
        denom = 2 * tp + fp + fn
        f1 = (2 * tp) / denom if denom > 0 else 0.0
        if f1 > best_f1:
            best_f1 = f1
            best_t = t
    return best_t


def compute_metrics(similarities: list, labels: list, threshold: float) -> dict:
    """
    Compute all metrics given similarity scores, true labels, and threshold.
    labels: 0=EQUIVALENT, 1=CHANGED
    Rule: predict CHANGED (1) if similarity < threshold.
    """
    n = len(similarities)
    tp = fp = fn = tn = 0
    for sim, lbl in zip(similarities, labels):
        pred = 1 if sim < threshold else 0
        if lbl == 1 and pred == 1:
            tp += 1
        elif lbl == 0 and pred == 1:
            fp += 1
        elif lbl == 1 and pred == 0:
            fn += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_denom = 2 * tp + fp + fn
    f1 = (2 * tp) / f1_denom if f1_denom > 0 else 0.0
    accuracy = (tp + tn) / n if n > 0 else 0.0

    auroc = compute_auroc(similarities, labels)
    auprc = compute_auprc(similarities, labels)

    # Bootstrap 95% CI for F1 and AUROC
    rng = random.Random(42)
    bs_f1, bs_auroc = [], []
    for _ in range(1000):
        idx = [rng.randint(0, n - 1) for _ in range(n)]
        bs_sims = [similarities[i] for i in idx]
        bs_lbls = [labels[i] for i in idx]
        bs_tp = bs_fp = bs_fn = 0
        for s, l in zip(bs_sims, bs_lbls):
            p = 1 if s < threshold else 0
            if l == 1 and p == 1:
                bs_tp += 1
            elif l == 0 and p == 1:
                bs_fp += 1
            elif l == 1 and p == 0:
                bs_fn += 1
        d = 2 * bs_tp + bs_fp + bs_fn
        bs_f1.append((2 * bs_tp) / d if d > 0 else 0.0)
        bs_auroc.append(compute_auroc(bs_sims, bs_lbls))

    bs_f1.sort()
    bs_auroc.sort()

    return {
        "accuracy": round(accuracy, 6),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "auroc": round(auroc, 6),
        "auprc": round(auprc, 6),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "n_samples": n,
        "threshold_used": round(threshold, 6),
        "ci_f1_lower": round(bs_f1[25], 6),
        "ci_f1_upper": round(bs_f1[974], 6),
        "ci_auroc_lower": round(bs_auroc[25], 6),
        "ci_auroc_upper": round(bs_auroc[974], 6),
    }


def save_results(baseline_name: str, split: str, results: dict,
                 artifact_dir: str = None):
    if artifact_dir is None:
        artifact_dir = str(ARTIFACTS_DIR / baseline_name)
    out_dir = pathlib.Path(artifact_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"results_{split}.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    return str(out_path)


def pairs_to_labels(pairs: list) -> list:
    """Convert pair dicts to int labels: 0=EQUIVALENT, 1=CHANGED."""
    return [0 if p["semantic_relation"] == EQUIV_LABEL else 1 for p in pairs]


def run_baseline(baseline_name: str, score_fn,
                 dev_pairs: list, test_pairs: list,
                 artifact_dir: str = None):
    """
    Standard baseline runner:
    1. Score dev pairs
    2. Find optimal threshold on dev
    3. Score test pairs
    4. Evaluate test with frozen dev threshold
    5. Save results
    Returns (dev_metrics, test_metrics, threshold)
    """
    print(f"\n[{baseline_name}] Scoring {len(dev_pairs)} dev pairs...")
    dev_labels = pairs_to_labels(dev_pairs)
    dev_sims = []
    for i, p in enumerate(dev_pairs):
        try:
            s = score_fn(load_source(p["base_path"]), load_source(p["variant_path"]))
        except Exception as e:
            s = 0.5  # neutral score on error
        dev_sims.append(float(s))
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(dev_pairs)} done")

    threshold = find_optimal_threshold(dev_sims, dev_labels)
    dev_metrics = compute_metrics(dev_sims, dev_labels, threshold)
    print(f"[{baseline_name}] DEV threshold={threshold:.4f} F1={dev_metrics['f1']:.4f} AUROC={dev_metrics['auroc']:.4f}")

    print(f"[{baseline_name}] Scoring {len(test_pairs)} test pairs...")
    test_labels = pairs_to_labels(test_pairs)
    test_sims = []
    for i, p in enumerate(test_pairs):
        try:
            s = score_fn(load_source(p["base_path"]), load_source(p["variant_path"]))
        except Exception as e:
            s = 0.5
        test_sims.append(float(s))
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(test_pairs)} done")

    test_metrics = compute_metrics(test_sims, test_labels, threshold)
    print(f"[{baseline_name}] TEST F1={test_metrics['f1']:.4f} AUROC={test_metrics['auroc']:.4f} AUPRC={test_metrics['auprc']:.4f}")

    dev_result = {
        "baseline": baseline_name,
        "split": "dev",
        "threshold": threshold,
        "metrics": dev_metrics,
        "score_distribution": {
            "eq_mean": round(sum(s for s, l in zip(dev_sims, dev_labels) if l == 0) /
                             max(1, sum(1 for l in dev_labels if l == 0)), 4),
            "ch_mean": round(sum(s for s, l in zip(dev_sims, dev_labels) if l == 1) /
                             max(1, sum(1 for l in dev_labels if l == 1)), 4),
        }
    }
    test_result = {
        "baseline": baseline_name,
        "split": "test",
        "threshold_from": "dev",
        "threshold": threshold,
        "metrics": test_metrics,
    }

    if artifact_dir is None:
        artifact_dir = str(ARTIFACTS_DIR / baseline_name)
    save_results(baseline_name, "dev", dev_result, artifact_dir)
    save_results(baseline_name, "test", test_result, artifact_dir)

    return dev_metrics, test_metrics, threshold
