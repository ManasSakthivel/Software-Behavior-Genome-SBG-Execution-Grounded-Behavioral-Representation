#!/usr/bin/env python3
"""
experiments/final/make_figures.py
=================================
Generates every figure from the authoritative artifacts. No number is typed in.

Figures are emitted as standalone SVG with no plotting dependency, so a
reproducer needs nothing beyond the standard library and the figures stay
diffable in git — a raster figure would hide a changed number inside a binary.

Each figure carries a caption naming its source artifact and its denominator,
because a bar chart without a denominator is how "744 test pairs" survived next
to a 643-pair measurement.

Usage:
    python3 experiments/final/make_figures.py [--out-dir docs/figures]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ARTIFACTS = REPO_ROOT / "artifacts" / "final"

# Colour-blind safe, and every series is also distinguishable by position and
# label, so the figures survive greyscale printing.
INK = "#1b1b1f"
MUTED = "#6b6b76"
GRID = "#d8d8de"
SERIES = {"sbg": "#2f6f9f", "reference": "#b8792a", "leak": "#9a3b3b",
          "neutral": "#7a7a85"}
FONT = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, "
        "'Helvetica Neue', Arial, sans-serif")


def esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def svg_header(width: int, height: int, title: str) -> List[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{esc(title)}">',
        f'<title>{esc(title)}</title>',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<style>text{{font-family:{FONT};fill:{INK}}} '
        f'.muted{{fill:{MUTED}}} .small{{font-size:11px}} '
        f'.tiny{{font-size:10px}} .bold{{font-weight:600}}</style>',
    ]


def load(name: str) -> Optional[dict]:
    path = ARTIFACTS / name
    return json.loads(path.read_text()) if path.exists() else None


# ---------------------------------------------------------------------------
# Figure 1 — AUROC with confidence intervals, both protocols
# ---------------------------------------------------------------------------

def figure_auroc(evaluations: Dict[str, dict], out: pathlib.Path) -> None:
    predictors = ["sbg_v5", "sbg_v3", "exception_component_v3",
                  "exception_fraction", "call_count", "combined_shortcut",
                  "static_ast", "static_token"]
    panels = [(label, payload) for label, payload in evaluations.items() if payload]
    if not panels:
        return

    row_h, top, left, panel_gap = 26, 74, 250, 58
    plot_w = 420
    panel_h = top + len(predictors) * row_h + 46
    height = panel_h * len(panels) + 30
    width = left + plot_w + 120

    lo, hi = 0.05, 0.80
    def x_of(value: float) -> float:
        return left + (value - lo) / (hi - lo) * plot_w

    parts = svg_header(width, height, "SBG AUROC by predictor and protocol")
    parts.append(f'<text x="20" y="28" class="bold" font-size="15">'
                 f'Main benchmark AUROC, statistically valid pairs</text>')
    parts.append(f'<text x="20" y="46" class="small muted">'
                 f'Bars are point estimates; whiskers are 95% cluster-bootstrap '
                 f'intervals resampling base programs. The structural baselines '
                 f'fall far below 0.5 \u2014 that inversion is the phenomenon '
                 f'execution is meant to resolve.</text>')

    for index, (label, payload) in enumerate(panels):
        y0 = 30 + index * panel_h
        block = payload["results"]["VALID"]["predictors"]
        n = payload["set_sizes"]["VALID"]
        clusters = next((v.get("n_clusters") for v in block.values()
                         if v.get("auroc") is not None), None)
        parts.append(f'<text x="20" y="{y0 + 26}" class="bold" font-size="13">'
                     f'{esc(label)}</text>')
        parts.append(f'<text x="20" y="{y0 + 42}" class="tiny muted">'
                     f'n = {n} pairs from {clusters} programs</text>')

        for tick in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
            x = x_of(tick)
            emphasis = tick == 0.50
            # Built outside the f-string: a backslash inside an f-string
            # expression is a SyntaxError before Python 3.12, and 3.9 is the
            # documented floor.
            dash = ' stroke-dasharray="4 3"' if emphasis else ''
            parts.append(
                f'<line x1="{x:.1f}" y1="{y0 + top - 16}" x2="{x:.1f}" '
                f'y2="{y0 + top + len(predictors) * row_h}" '
                f'stroke="{INK if emphasis else GRID}" '
                f'stroke-width="{1.2 if emphasis else 1}"{dash}/>')
            parts.append(f'<text x="{x:.1f}" y="{y0 + top - 22}" '
                         f'text-anchor="middle" class="tiny muted">{tick:.2f}</text>')

        noise = payload["results"]["VALID"].get("label_shuffle_noise_floor_primary")
        if noise:
            x = x_of(noise["p95"])
            parts.append(
                f'<line x1="{x:.1f}" y1="{y0 + top - 16}" x2="{x:.1f}" '
                f'y2="{y0 + top + len(predictors) * row_h}" stroke="{SERIES["leak"]}" '
                f'stroke-width="1.4" stroke-dasharray="2 3"/>')
            parts.append(
                f'<text x="{x + 4:.1f}" y="{y0 + top + len(predictors) * row_h + 14}" '
                f'class="tiny" fill="{SERIES["leak"]}">noise floor '
                f'{noise["p95"]:.3f}</text>')

        for row, name in enumerate(predictors):
            stats = block.get(name)
            if not stats or stats.get("auroc") is None:
                continue
            y = y0 + top + row * row_h
            colour = (SERIES["sbg"] if name.startswith("sbg")
                      else SERIES["leak"] if "exception" in name
                      else "#5a7a5a" if name.startswith("static")
                      else SERIES["reference"])
            parts.append(f'<text x="{left - 12}" y="{y + 13}" text-anchor="end" '
                         f'class="small">{esc(name)}</text>')
            x_zero, x_val = x_of(lo), x_of(stats["auroc"])
            parts.append(
                f'<rect x="{x_zero:.1f}" y="{y + 4}" width="{max(0, x_val - x_zero):.1f}" '
                f'height="14" fill="{colour}" opacity="0.30"/>')
            ci = stats["ci95_cluster_bootstrap"]
            x_lo, x_hi = x_of(max(lo, ci[0])), x_of(min(hi, ci[1]))
            parts.append(f'<line x1="{x_lo:.1f}" y1="{y + 11}" x2="{x_hi:.1f}" '
                         f'y2="{y + 11}" stroke="{colour}" stroke-width="1.6"/>')
            for cap in (x_lo, x_hi):
                parts.append(f'<line x1="{cap:.1f}" y1="{y + 6}" x2="{cap:.1f}" '
                             f'y2="{y + 16}" stroke="{colour}" stroke-width="1.6"/>')
            parts.append(f'<circle cx="{x_val:.1f}" cy="{y + 11}" r="3.6" '
                         f'fill="{colour}"/>')
            parts.append(f'<text x="{x_of(hi) + 10}" y="{y + 15}" class="tiny">'
                         f'{stats["auroc"]:.3f} [{ci[0]:.3f}, {ci[1]:.3f}]</text>')

    parts.append('</svg>')
    out.write_text("\n".join(parts) + "\n")


# ---------------------------------------------------------------------------
# Figure 2 — where the 744 pairs go
# ---------------------------------------------------------------------------

def figure_denominators(payload: dict, manifest: dict, out: pathlib.Path) -> None:
    sizes = payload["set_sizes"]
    ledger = payload["failure_ledger"]
    test = manifest["datasets"]["v5_published"]["splits"]["test"]

    width, height = 1020, 380
    parts = svg_header(width, height, "Where the test split's pairs go")
    parts.append('<text x="20" y="28" class="bold" font-size="15">'
                 'Every pair in the test split, accounted for</text>')
    parts.append('<text x="20" y="46" class="small muted">'
                 'The published AUROC was reported against the first bar and '
                 'computed on the second.</text>')

    bars = [
        ("nominal pairs in the split", sizes["ALL"], SERIES["neutral"]),
        ("executed under the protocol", sizes["EVALUABLE"], SERIES["reference"]),
        ("also statistically valid", sizes["VALID"], SERIES["sbg"]),
    ]
    left, top, bar_h, gap = 250, 76, 26, 16
    scale = 640 / max(1, sizes["ALL"])
    for index, (label, value, colour) in enumerate(bars):
        y = top + index * (bar_h + gap)
        parts.append(f'<text x="{left - 12}" y="{y + 18}" text-anchor="end" '
                     f'class="small">{esc(label)}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{value * scale:.1f}" '
                     f'height="{bar_h}" fill="{colour}" opacity="0.75"/>')
        parts.append(f'<text x="{left + value * scale + 8:.1f}" y="{y + 18}" '
                     f'class="small bold">{value}</text>')

    y = top + 3 * (bar_h + gap) + 24
    parts.append(f'<text x="20" y="{y}" class="small bold">'
                 f'Not executed ({sizes["ALL"] - sizes["EVALUABLE"]} pairs)</text>')
    for index, (cause, count) in enumerate(sorted(ledger.items())):
        parts.append(f'<text x="34" y="{y + 20 + index * 16}" class="tiny">'
                     f'{esc(cause)}</text>')
        parts.append(f'<rect x="300" y="{y + 10 + index * 16}" '
                     f'width="{count * 2.2:.1f}" height="11" '
                     f'fill="{SERIES["leak"]}" opacity="0.6"/>')
        parts.append(f'<text x="{300 + count * 2.2 + 6:.1f}" '
                     f'y="{y + 20 + index * 16}" class="tiny">{count}</text>')

    y2 = y + 20 + len(ledger) * 16 + 18
    parts.append(f'<text x="20" y="{y2}" class="small bold">'
                 f'Executed but statically invalid '
                 f'({sizes["EVALUABLE"] - sizes["VALID"]} pairs)</text>')
    invalid = [("CHANGED, mutation unreachable from the entry function",
                test["excluded_changed_unobservable"])]
    for index, (cause, count) in enumerate(invalid):
        parts.append(f'<text x="34" y="{y2 + 20 + index * 16}" class="tiny">'
                     f'{esc(cause)}</text>')
        parts.append(f'<text x="560" y="{y2 + 20 + index * 16}" class="tiny bold">'
                     f'{count} of {test["changed_pairs"]} CHANGED pairs</text>')
    parts.append('</svg>')
    out.write_text("\n".join(parts) + "\n")


# ---------------------------------------------------------------------------
# Figure 3 — SBG versus the output-reading reference
# ---------------------------------------------------------------------------

def figure_oracle_gap(hard: dict, regression: dict, out: pathlib.Path) -> None:
    rows: List[Tuple[str, int, int, int, int]] = []
    for regime in ("canonical", "declared"):
        metrics = hard["regimes"][regime]["metrics"]
        sbg = metrics["sbg_v5_output_free"]
        ref = metrics["output_reading_reference"]
        rows.append((f"Hard negatives ({regime} inputs)",
                     sbg["tp"] + sbg["tn"], sbg["n_scored"],
                     ref["tp"] + ref["tn"], ref["n_scored"]))
    sbg = regression["all_pairs"]["sbg_v5_output_free"]
    ref = regression["all_pairs"]["output_reading_reference_full_behaviour"]
    rows.append(("Regression corpus", sbg["n_detected"], sbg["n_scored"],
                 ref["n_detected"], ref["n_total"]))
    silent = regression["silent_bugs_only"]
    rows.append(("Silent bugs only",
                 silent["sbg_v5_output_free"]["n_detected"],
                 silent["sbg_v5_output_free"]["n_scored"],
                 silent["output_reading_reference"]["n_detected"],
                 silent["output_reading_reference"]["n_total"]))

    width, height = 940, 132 + len(rows) * 56
    parts = svg_header(width, height, "SBG versus the output-reading reference")
    parts.append('<text x="20" y="28" class="bold" font-size="15">'
                 'Output-free SBG against an output-reading reference</text>')
    parts.append('<text x="20" y="46" class="small muted">'
                 'The reference reads program outputs. Earlier releases reported '
                 'its scores as SBG results.</text>')
    for offset, (colour, name) in enumerate((
            (SERIES["sbg"], "SBG V5, output-free"),
            (SERIES["reference"], "output-reading reference"))):
        x = 20 + offset * 210
        parts.append(f'<rect x="{x}" y="58" width="14" height="10" fill="{colour}" '
                     f'opacity="0.8"/>')
        parts.append(f'<text x="{x + 20}" y="67" class="tiny">{esc(name)}</text>')

    left, bar_w = 330, 460
    for index, (label, sbg_n, sbg_total, ref_n, ref_total) in enumerate(rows):
        y = 96 + index * 56
        parts.append(f'<text x="{left - 12}" y="{y + 12}" text-anchor="end" '
                     f'class="small">{esc(label)}</text>')
        for offset, (value, total, colour, name) in enumerate((
                (sbg_n, sbg_total, SERIES["sbg"], "SBG V5, output-free"),
                (ref_n, ref_total, SERIES["reference"], "output-reading reference"))):
            yy = y + offset * 20
            frac = value / total if total else 0.0
            parts.append(f'<rect x="{left}" y="{yy}" width="{bar_w}" height="14" '
                         f'fill="{GRID}"/>')
            parts.append(f'<rect x="{left}" y="{yy}" width="{bar_w * frac:.1f}" '
                         f'height="14" fill="{colour}" opacity="0.8"/>')
            parts.append(f'<text x="{left + bar_w + 8}" y="{yy + 12}" class="tiny">'
                         f'{value}/{total}</text>')
    parts.append(f'<text x="20" y="{height - 14}" class="tiny muted">'
                 f'Threshold tau* = {regression["threshold_tau_star"]}, fixed in '
                 f'advance. Sources: HARD_NEGATIVE_V5_RESULTS.json, '
                 f'REGRESSION_V5_RESULTS.json</text>')
    parts.append('</svg>')
    out.write_text("\n".join(parts) + "\n")


# ---------------------------------------------------------------------------
# Figure 4 — the protocol leak
# ---------------------------------------------------------------------------

def figure_leak(leak: dict, out: pathlib.Path) -> None:
    summary = leak["corpus_summary"]
    width, height = 960, 372
    parts = svg_header(width, height, "Output-free constraint: protocol audit")
    parts.append('<text x="20" y="28" class="bold" font-size="15">'
                 'What the published protocol actually traces</text>')
    parts.append('<text x="20" y="46" class="small muted">'
                 'Static analysis of all 64 corpus programs. No program is '
                 'executed.</text>')

    total = summary["n_programs"]
    left, bar_w = 360, 440
    rows = [
        ("corpus programs", total, SERIES["neutral"]),
        ("entry point is a self-test driver", summary["n_entry_is_self_test_driver"],
         SERIES["leak"]),
        ("assert statements land inside the trace",
         summary["n_entry_traces_assertions"], SERIES["leak"]),
        ("canonical inputs never execute",
         summary["n_canonical_inputs_unused"], SERIES["reference"]),
    ]
    for index, (label, value, colour) in enumerate(rows):
        y = 80 + index * 34
        parts.append(f'<text x="{left - 12}" y="{y + 14}" text-anchor="end" '
                     f'class="small">{esc(label)}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{bar_w}" height="18" '
                     f'fill="{GRID}"/>')
        parts.append(f'<rect x="{left}" y="{y}" width="{bar_w * value / total:.1f}" '
                     f'height="18" fill="{colour}" opacity="0.8"/>')
        parts.append(f'<text x="{left + bar_w + 8}" y="{y + 14}" class="small">'
                     f'{value} / {total}</text>')

    y = 80 + len(rows) * 34 + 26
    caption = [
        "Entry-point discovery returns the call-graph root, defined as the function no",
        "other module-level function calls. In this corpus that is the program's own",
        f"test_* self-test driver. Its assert statements -- "
        f"{summary['total_assert_statements_traced']} of them across the corpus --",
        "then execute inside the traced region, so exception_rate and exception_type_set",
        "record whether the program's own unit tests passed.",
    ]
    for index, line in enumerate(caption):
        parts.append(f'<text x="20" y="{y + index * 16}" class="tiny">'
                     f'{esc(line)}</text>')
    parts.append('</svg>')
    out.write_text("\n".join(parts) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(REPO_ROOT / "docs" / "figures"))
    args = parser.parse_args()
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    evaluations = {
        "Published protocol (traces self-test drivers)":
            load("MAIN_EVALUATION_test_published.json"),
        "Output-free protocol v6":
            load("MAIN_EVALUATION_test_output_free_v6.json"),
        "Output-free protocol v6, corrected benchmark":
            load("MAIN_EVALUATION_v6test_output_free_v6.json"),
    }
    manifest = json.loads((REPO_ROOT / "benchmark" / "benchmark_manifest.json").read_text())
    hard = load("HARD_NEGATIVE_V5_RESULTS.json")
    regression = load("REGRESSION_V5_RESULTS.json")
    leak = load("OUTPUT_ORACLE_LEAK_AUDIT.json")

    written = []
    if any(evaluations.values()):
        figure_auroc(evaluations, out_dir / "fig1_auroc.svg")
        written.append("fig1_auroc.svg")
    published = evaluations["Published protocol (traces self-test drivers)"]
    if published:
        figure_denominators(published, manifest, out_dir / "fig2_denominators.svg")
        written.append("fig2_denominators.svg")
    if hard and regression:
        figure_oracle_gap(hard, regression, out_dir / "fig3_oracle_gap.svg")
        written.append("fig3_oracle_gap.svg")
    if leak:
        figure_leak(leak, out_dir / "fig4_protocol_leak.svg")
        written.append("fig4_protocol_leak.svg")

    for name in written:
        print(f"wrote docs/figures/{name}")
    if not written:
        print("no artifacts available; nothing generated", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
