"""Blinded adjudication workflow model (Phase 3 tooling; no adjudicator or decision is ever fabricated here).
Blinding is structural: AdjudicationCase has no field for model scores, ERS outputs, baseline predictions or verdicts, and any
such key in any nested input raises BlindingViolation. The audit log is an append-only JSONL hash chain: TAMPER-EVIDENT ONLY
(an editor of the whole file can recompute every hash; there is no signature or external anchor)."""
from __future__ import annotations
import dataclasses, datetime, hashlib, json, os, re
from dataclasses import dataclass, field
from itertools import product

CONFIRMED, NONE_FOUND, UNRESOLVED = "confirmed_divergence", "no_divergence_found_within_budget", "unresolved"
OUTCOMES = (CONFIRMED, NONE_FOUND, UNRESOLVED)
FORBIDDEN = re.compile(r"(score|risk|verdict|(^|[_\W])ers([_\W]|$)|baseline|predict|model|v7b|profile|feature|confidence|probab)", re.I)

class BlindingViolation(ValueError): pass
class BudgetFrozen(RuntimeError): pass

def check_blind(obj, path="case"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if FORBIDDEN.search(str(k)): raise BlindingViolation(f"forbidden key {path}.{k}")
            check_blind(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj): check_blind(v, f"{path}[{i}]")

@dataclass(frozen=True)
class AdjudicationCase:
    pair_id: str
    observation_boundary: dict            # frozen scope O (channels counted)
    budget: dict                          # frozen budget b, e.g. {"generators": 5, "time_cap_s": 600, "seeds": [..]}
    evidence_reviewed: tuple = ()         # identifiers of artefacts the adjudicator may see (diff, adjudication-only inputs)
    def __post_init__(self):
        check_blind({"observation_boundary": self.observation_boundary, "budget": self.budget, "evidence_reviewed": list(self.evidence_reviewed)})
        if not self.pair_id: raise ValueError("pair_id required")
    @staticmethod
    def from_dict(d):
        names = {f.name for f in dataclasses.fields(AdjudicationCase)}
        for k in d:
            if k not in names:
                raise BlindingViolation(f"unknown/forbidden field {k!r}") if FORBIDDEN.search(k) else ValueError(f"unknown field {k!r}")
        return AdjudicationCase(d["pair_id"], d["observation_boundary"], d["budget"], tuple(d.get("evidence_reviewed", ())))
    def budget_hash(self): return _canon_hash(self.budget)

def _canon_hash(o): return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
def _now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()

class Workflow:
    """State is rebuilt by replaying the JSONL hash chain at `log_path`. roles: 'primary' (exactly two distinct adjudicators) and
    'third' (only after the primaries disagree, distinct from both)."""
    def __init__(self, log_path, clock=_now):
        self.path, self.clock = log_path, clock
        self.cases, self.decisions, self.resolutions = {}, {}, {}
        self._last = "0" * 64; self._seq = 0
        if os.path.exists(log_path):
            ok, msg = verify_chain(log_path)
            if not ok: raise ValueError("audit chain invalid: " + msg)
            for e in _events(log_path): self._apply(e)

    def _append(self, typ, payload):
        e = {"seq": self._seq + 1, "ts": self.clock(), "type": typ, "payload": payload, "prev": self._last}
        e["hash"] = _canon_hash({k: e[k] for k in ("seq", "ts", "type", "payload", "prev")})
        with open(self.path, "a") as f: f.write(json.dumps(e, sort_keys=True) + "\n")
        self._apply(e)

    def _apply(self, e):
        self._seq, self._last, p = e["seq"], e["hash"], e["payload"]
        if e["type"] in ("case_registered", "budget_set"):
            self.cases[p["pair_id"]] = AdjudicationCase.from_dict(p)
        elif e["type"] == "decision": self.decisions.setdefault(p["pair_id"], []).append(p)

    def register_case(self, case):
        if case.pair_id in self.cases: raise ValueError("case already registered")
        self._append("case_registered", dataclasses.asdict(case))

    def set_budget(self, pair_id, budget):
        c = self.cases[pair_id]
        if self.decisions.get(pair_id): raise BudgetFrozen(f"{pair_id}: budget frozen after first decision")
        self._append("budget_set", dataclasses.asdict(dataclasses.replace(c, budget=budget)))

    def record_decision(self, pair_id, adjudicator, outcome, rationale, role="primary"):
        c = self.cases[pair_id]; ds = self.decisions.get(pair_id, [])
        if outcome not in OUTCOMES: raise ValueError(f"outcome must be one of {OUTCOMES}")
        if not rationale.strip(): raise ValueError("rationale required")
        if any(d["adjudicator"] == adjudicator for d in ds): raise ValueError("adjudicator already decided this case")
        prim = [d for d in ds if d["role"] == "primary"]
        if role == "primary" and len(prim) >= 2: raise ValueError("two primary decisions already recorded")
        if role == "third":
            if len(prim) < 2 or prim[0]["outcome"] == prim[1]["outcome"]: raise ValueError("third adjudicator only after primary disagreement")
            if any(d["role"] == "third" for d in ds): raise ValueError("third decision already recorded")
        elif role != "primary": raise ValueError("role must be primary|third")
        self._append("decision", {"pair_id": pair_id, "adjudicator": adjudicator, "role": role, "outcome": outcome, "rationale": rationale,
                                  "decided_at": self.clock(), "budget_hash": c.budget_hash()})

    def final_outcome(self, pair_id):
        """(outcome, route): route in agreed | third_resolved | pending_third | pending_primaries. Never invents an outcome."""
        ds = self.decisions.get(pair_id, [])
        prim = [d for d in ds if d["role"] == "primary"]; third = [d for d in ds if d["role"] == "third"]
        if len(prim) < 2: return UNRESOLVED, "pending_primaries"
        if prim[0]["outcome"] == prim[1]["outcome"]: return prim[0]["outcome"], "agreed"
        if third: return third[0]["outcome"], "third_resolved"
        return UNRESOLVED, "pending_third"

    def outcomes(self): return {p: self.final_outcome(p)[0] for p in sorted(self.cases)}

def _events(path):
    with open(path) as f: return [json.loads(l) for l in f if l.strip()]

def verify_chain(path):
    prev, n = "0" * 64, 0
    for e in _events(path):
        n += 1
        h = _canon_hash({k: e[k] for k in ("seq", "ts", "type", "payload", "prev")})
        if e["seq"] != n or e["prev"] != prev or e["hash"] != h: return False, f"break at seq {n}"
        prev = e["hash"]
    return True, f"{n} events"

# ---- agreement ----
def confusion_matrix(a, b, labels=OUTCOMES):
    m = {x: {y: 0 for y in labels} for x in labels}
    for x, y in zip(a, b): m[x][y] += 1
    return m

def cohen_kappa(a, b, labels=OUTCOMES):
    """Returns dict(kappa, po, pe, n, note). Degenerate marginals (pe == 1, i.e. both raters use one identical category): kappa is
    undefined -> None with a note; report raw agreement instead. n == 0 -> None. No smoothing is applied."""
    n = len(a)
    if n == 0 or n != len(b): return {"kappa": None, "po": None, "pe": None, "n": n, "note": "empty or mismatched ratings"}
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((sum(x == l for x in a) / n) * (sum(y == l for y in b) / n) for l in labels)
    if abs(1 - pe) < 1e-12:
        return {"kappa": None, "po": po, "pe": pe, "n": n, "note": "degenerate marginals (single shared category): kappa undefined; report raw agreement"}
    return {"kappa": (po - pe) / (1 - pe), "po": po, "pe": pe, "n": n, "note": ""}

def agreement_report(wf, kappa_min=0.7, min_double_fraction=0.30):
    pairs = [(p, [d for d in wf.decisions.get(p, []) if d["role"] == "primary"]) for p in sorted(wf.cases)]
    dbl = [(p, ds) for p, ds in pairs if len(ds) == 2]
    a, b = [ds[0]["outcome"] for _, ds in dbl], [ds[1]["outcome"] for _, ds in dbl]
    k = cohen_kappa(a, b)
    routes = [wf.final_outcome(p)[1] for p in wf.cases]
    frac = len(dbl) / len(pairs) if pairs else 0.0
    return {"n_cases": len(pairs), "n_double_labelled": len(dbl), "double_labelled_fraction": frac,
            "kappa": k, "confusion": confusion_matrix(a, b), "n_disagreements": sum(x != y for x, y in zip(a, b)),
            "n_third_resolved": routes.count("third_resolved"), "n_pending": routes.count("pending_third") + routes.count("pending_primaries"),
            "n_final_unresolved": sum(o == UNRESOLVED for o in wf.outcomes().values()),
            "meets_kappa": k["kappa"] is not None and k["kappa"] >= kappa_min,
            "meets_double_coverage": frac >= min_double_fraction,
            "note": "protocol 07: kappa >= 0.7 on >= 30% double-labelled (all divergent pairs double-labelled; the latter is not checkable here)"}

# ---- outcome -> y ----
VARIANTS = ("drop", "worst_case_divergence", "non_divergence")
def y_from_adjudication(outcome, unresolved="drop"):
    """confirmed -> 1, none_found -> 0. unresolved: 'drop' -> None (excluded, counted); 'worst_case_divergence' -> 1; 'non_divergence' -> 0."""
    if outcome == CONFIRMED: return 1
    if outcome == NONE_FOUND: return 0
    if outcome != UNRESOLVED: raise ValueError(f"unknown outcome {outcome!r}")
    if unresolved not in VARIANTS: raise ValueError(f"unresolved must be one of {VARIANTS}")
    return {"drop": None, "worst_case_divergence": 1, "non_divergence": 0}[unresolved]

def estimand_variants(outcomes, issued=None):
    """outcomes: {pair_id: outcome}. Returns {variant: {'y': {pair: y}, 'n_unresolved', ['risk','n_issued']}}.
    issued (optional): set of pair_ids with an NDO verdict -> selective risk R = mean y over issued pairs with y not None (None if empty).
    Note: dropping unresolved changes numerator and denominator (04 sec 7)."""
    out = {}
    for v in VARIANTS:
        y = {p: y_from_adjudication(o, v) for p, o in sorted(outcomes.items())}
        d = {"y": {p: l for p, l in y.items() if l is not None}, "n_unresolved": sum(o == UNRESOLVED for o in outcomes.values())}
        if issued is not None:
            ys = [y[p] for p in sorted(issued) if p in y and y[p] is not None]
            d["n_issued"], d["risk"] = len(ys), (sum(ys) / len(ys) if ys else None)
        out[v] = d
    return out
