"""Project-aware splitting, leakage checks, nested grouped folds, family-shift split, and the holdout label guard.
No function here ever splits a project (or, with group='family', a family). Assignment is a deterministic function of
(seed, group name): no reliance on hash/dict order. This module NEVER creates an unlock token."""
from __future__ import annotations
import hashlib, json, os, datetime
from collections import defaultdict

SPLITS = ("development", "calibration", "evaluation", "holdout")

def _get(x, k, default=None):
    return x.get(k, default) if isinstance(x, dict) else getattr(x, k, default)

def _h(seed, name):
    return hashlib.sha256(f"{seed}|{name}".encode()).hexdigest()

def _groups(items, group):
    g = defaultdict(list)
    for x in items: g[_get(x, group)].append(x)
    return g

def _allocate(groups, order_key, fractions):
    """Deficit allocation of whole groups to splits; weights are pair counts. Returns {group: split}."""
    fr = {s: f for s, f in fractions.items() if f > 0}
    tot = sum(len(v) for v in groups.values()); cur = dict.fromkeys(fr, 0); out = {}
    for g in sorted(groups, key=order_key):
        n = len(groups[g])
        s = max(sorted(fr), key=lambda s: (fr[s] * tot - cur[s]) / (fr[s] * tot))
        out[g] = s; cur[s] += n
    return out

def project_split(items, seed, fractions=None, group="project", strata=None):
    """items: manifest rows, EvidenceRecords or dicts (need pair_id, project, family). group: 'project'|'family'.
    strata: optional fn(list_of_items_in_group)->key; groups are ordered stratum-first so each stratum is spread across splits.
    Returns {'group','seed','fractions','by_group','rows':[(pair_id, project, family, split)]}."""
    fractions = fractions or {"development": .5, "calibration": .2, "evaluation": .3}
    if group not in ("project", "family"): raise ValueError("group must be 'project' or 'family'")
    assert abs(sum(fractions.values()) - 1) < 1e-9 and set(fractions) <= set(SPLITS), "fractions must sum to 1 over known splits"
    gs = _groups(items, group)
    sk = {g: (str(strata(v)) if strata else "") for g, v in gs.items()}
    by_group = _allocate(gs, lambda g: (sk[g], _h(seed, g)), fractions)
    rows = sorted((_get(x, "pair_id"), _get(x, "project"), _get(x, "family"), by_group[_get(x, group)]) for x in items)
    return {"group": group, "seed": seed, "fractions": dict(fractions), "by_group": by_group, "rows": rows}

def assert_no_leakage(assignment, families=False):
    """Raise AssertionError when a project (and, if families=True, a family) appears in more than one split."""
    for key, i in (("project", 1),) + ((("family", 2),) if families else ()):
        seen = defaultdict(set)
        for r in assignment["rows"]: seen[r[i]].add(r[3])
        bad = {k: sorted(v) for k, v in seen.items() if len(v) > 1}
        assert not bad, f"{key} leakage across splits: {bad}"
    return True

def nested_group_folds(items, seed, outer_k=5, inner_k=3, group="project"):
    """Yield dicts {outer, train_groups, test_groups, inner:[{train_groups,val_groups}]}; every fold is group-disjoint."""
    gs = _groups(items, group)
    def kfold(names, k, tag):
        k = min(k, len(names))
        if k < 2: raise ValueError("need at least 2 groups for folds")
        sub = {g: gs[g] for g in names}
        a = _allocate(sub, lambda g: _h(f"{seed}|{tag}", g), {str(i): 1 / k for i in range(k)})
        return [sorted(g for g, f in a.items() if f == str(i)) for i in range(k)]
    outer = kfold(sorted(gs), outer_k, "outer")
    for i, test in enumerate(outer):
        train = sorted(g for j, f in enumerate(outer) if j != i for g in f)
        inner = kfold(train, inner_k, f"inner{i}")
        yield {"outer": i, "train_groups": train, "test_groups": test,
               "inner": [{"train_groups": sorted(g for j, f in enumerate(inner) if j != m for g in f), "val_groups": inner[m]} for m in range(len(inner))]}

# ---- distribution shift (see reports/v8/V8_DISTRIBUTION_SHIFT_PROTOCOL.md) ----
def family_shift_feasibility(items, min_families=3, min_projects_per_family=5, min_labelled_pairs_per_family=20, max_family_share=0.6):
    """Report whether the data supports a project-family shift experiment, and why not. Counts only labelled (y in 0/1) pairs."""
    fam = defaultdict(lambda: {"projects": set(), "pairs": 0, "labelled": 0, "y1": 0})
    for x in items:
        d = fam[_get(x, "family")]; d["projects"].add(_get(x, "project")); d["pairs"] += 1
        y = _get(x, "y")
        if y in (0, 1): d["labelled"] += 1; d["y1"] += y
    tot = sum(d["labelled"] for d in fam.values()) or 1
    table = {f: {"projects": len(d["projects"]), "pairs": d["pairs"], "labelled": d["labelled"], "y1": d["y1"]} for f, d in sorted(fam.items())}
    ok = [f for f, d in table.items() if d["projects"] >= min_projects_per_family and d["labelled"] >= min_labelled_pairs_per_family and d["y1"] > 0 and d["labelled"] > d["y1"]]
    why = []
    if len(ok) < min_families: why.append(f"only {len(ok)} families ({ok}) have >= {min_projects_per_family} projects, >= {min_labelled_pairs_per_family} labelled pairs and both classes; need {min_families}")
    for f, d in table.items():
        if d["labelled"] / tot > max_family_share: why.append(f"family {f!r} holds {d['labelled'] / tot:.0%} of labelled pairs (> {max_family_share:.0%})")
    for f, d in table.items():
        if f not in ok: why.append(f"family {f!r} ineligible: {d}")
    return {"feasible": not why, "eligible_families": ok, "families": table, "reasons": why,
            "verdict": "FEASIBLE" if not why else "DEFERRED: data lacks family diversity"}

def family_shift_split(items, seed, held_out_families=None, n_held_out=1, calib_fraction=0.3):
    """Train/calibrate on some families, evaluate on held-out families. Within train families projects are split (project-aware) into
    development/calibration. Refuses (ValueError) if fewer than 2 families. Returns an assignment usable by assert_no_leakage(families=False)
    (calibration/development share families by design; held-out families are disjoint: checked with assert_heldout_families)."""
    fams = sorted({_get(x, "family") for x in items})
    if len(fams) < 2: raise ValueError("family shift needs >= 2 families")
    if held_out_families is None:
        held_out_families = sorted(fams, key=lambda f: _h(seed, f))[:n_held_out]
    held = set(held_out_families)
    if not held or held >= set(fams): raise ValueError("need at least one held-out and one training family")
    train = [x for x in items if _get(x, "family") not in held]
    a = project_split(train, seed, {"development": 1 - calib_fraction, "calibration": calib_fraction})
    rows = a["rows"] + [(_get(x, "pair_id"), _get(x, "project"), _get(x, "family"), "evaluation") for x in items if _get(x, "family") in held]
    a.update(rows=sorted(rows), held_out_families=sorted(held), group="family-shift")
    a["by_group"].update({p: "evaluation" for _, p, f, _s in a["rows"] if f in held})
    assert_heldout_families(a); assert_no_leakage(a)
    return a

def assert_heldout_families(a):
    ev = {r[2] for r in a["rows"] if r[3] == "evaluation"}; tr = {r[2] for r in a["rows"] if r[3] != "evaluation"}
    assert not (ev & tr), f"families in both train and evaluation: {sorted(ev & tr)}"
    return True

# ---- holdout guard ----
class HoldoutLocked(PermissionError):
    pass

class HoldoutGuard:
    """Reading labels of holdout rows raises unless `token_path` is given AND the file exists. The module never writes a token;
    unlocking is a Phase 3 action requiring explicit user authorisation. Every attempt (allowed or refused) is logged in `.log`
    and, if `log_path` is given, appended to that JSONL file."""
    def __init__(self, token_path=None, log_path=None):
        self.token_path, self.log_path, self.log = token_path, log_path, []

    @property
    def unlocked(self): return bool(self.token_path) and os.path.isfile(self.token_path)

    def _record(self, what, n, allowed):
        e = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(), "what": what, "n_holdout_rows": n, "allowed": allowed,
             "token_path": self.token_path}
        self.log.append(e)
        if self.log_path:
            with open(self.log_path, "a") as f: f.write(json.dumps(e, sort_keys=True) + "\n")

    def labels(self, items, what="labels"):
        """Return {pair_id: y} for non-holdout rows; for holdout rows require the unlock token."""
        hold = [x for x in items if _get(x, "split") == "holdout"]
        if hold:
            self._record(what, len(hold), self.unlocked)
            if not self.unlocked: raise HoldoutLocked(f"{len(hold)} holdout rows: labels locked (no unlock token); attempt logged")
        return {_get(x, "pair_id"): _get(x, "y") for x in items}

def strip_holdout_labels(items):
    """Return dict copies of items with y/outcome removed for holdout rows (safe default view)."""
    out = []
    for x in items:
        d = dict(x) if isinstance(x, dict) else dict(x.__dict__)
        if d.get("split") == "holdout": d.update(y=None, outcome_class="sealed", label_source="")
        out.append(d)
    return out
