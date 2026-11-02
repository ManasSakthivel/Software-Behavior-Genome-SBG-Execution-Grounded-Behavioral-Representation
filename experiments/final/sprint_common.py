"""Shared loaders for the FINAL SPRINT analyses (read-only over frozen artifacts).

Nothing here writes to a frozen artifact.  Populations are reconstructed exactly as the frozen
evaluators do (evaluate_v9.load/matched_complete for v9c; evaluate_v10.stage_run row-building for v10).
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "experiments" / "final"))
import evaluate_v9 as e                                                                  # noqa: E402
from edit_size_analysis import _edit_size                                                # noqa: E402
from static_baselines import token_multiset, ast_multiset, multiset_distance             # noqa: E402

ART, EV = e.ART, e.EV
V10 = REPO / "benchmark" / "datasets" / "v10_independent"
V10_SCORED = ART / "pairs_v10_test_v6exp.jsonl"
V10_MODELS = ART / "V10_MODELS_FROZEN.json"
OUT = EV


def load_v10_population():
    """Matched-complete V10 population (638 pairs), identical to evaluate_v10.stage_run, plus metadata."""
    meta = {m["pair_id"]: m for m in e.jl(V10 / "pairs_test.jsonl")}
    scored = {r["pair_id"]: r for r in e.jl(V10_SCORED)}
    rows = []
    for pid, m in meta.items():
        r = scored[pid]
        if not r["evaluated"]:
            continue
        sc = dict(r["scores"])
        sc["sbg_v6"], sc["sbg_state_v6"] = r["sbg_v6"], r["sbg_state_v6"]
        sc["edit"] = float(_edit_size(m["base_path"], m["variant_path"]))
        bs, vs = (REPO / m["base_path"]).read_text(), (REPO / m["variant_path"]).read_text()
        sc["static_token"] = multiset_distance(token_multiset(bs), token_multiset(vs))
        sc["static_ast"] = multiset_distance(ast_multiset(bs), ast_multiset(vs))
        rows.append({"pair_id": pid, "base_id": m["base_id"], "label": int(m["semantic_relation"] == "CHANGED"),
                     "group": m["pair_id"] if m["semantic_relation"] == "EQUIVALENT" else m["matched_pair_id"],
                     "transformation_type": m["transformation_type"], "sc_type": m.get("sc_type"), "sp_type": m.get("sp_type"),
                     "base_path": m["base_path"], "variant_path": m["variant_path"], "_edit": int(sc["edit"]), "scores": sc})
    ok = collections.defaultdict(list)
    for r in rows:
        ok[r["group"]].append(r)
    pop = [x for g in ok.values() if len(g) == 2 and {y["label"] for y in g} == {0, 1} for x in g]
    models = json.loads(V10_MODELS.read_text())["models"]
    for r in pop:
        for n, m in models.items():
            r["scores"][f"M_{n}"] = e.lin_score(m, m["features"], r["scores"])
    return pop, models


def load_v9c_population(split):
    rows = e.load("v9c", split)
    pop = e.matched_complete(rows)
    models = json.loads(e.MODELS_FILE.read_text())["models"]
    for r in pop:
        for n, m in models.items():
            r["scores"][f"M_{n}"] = e.lin_score(m, m["features"], r["scores"])
        # aliases so v9c models (E, ES, EX, ESX) and v10 models (E, E+V5, EX, EX+V5) share predictor names
        r["scores"]["M_E+V5"], r["scores"]["M_EX+V5"] = r["scores"]["M_ES"], r["scores"]["M_ESX"]
    return pop


def matched_sets(pop):
    """group -> {0: equivalent row, 1: changed row}"""
    g = collections.defaultdict(dict)
    for r in pop:
        g[r["group"]][r["label"]] = r
    return {k: v for k, v in g.items() if 0 in v and 1 in v}


def set_outcome(s, pred):
    c, q = s[1]["scores"][pred], s[0]["scores"][pred]
    return 1.0 if c > q else 0.5 if c == q else 0.0
