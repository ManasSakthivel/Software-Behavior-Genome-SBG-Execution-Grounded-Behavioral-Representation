"""Evidence perturbations P1..P9 (post-hoc on recorded evidence; real-execution variants need the collector and are flagged).
apply() is deterministic given (rec, pid, params, seed), never mutates its input, and never reads rec.y / rec.meta."""
from __future__ import annotations
import copy, hashlib, json, random
from dataclasses import dataclass, asdict, field
from sbgv8.schema import InputEvidence, PERTURBATIONS

_ET = ["static_coverage", "repeat_runs", "observations", "provenance", "integrity", "environment"]
def _v(**k): return {e: k.get(e, "n/a") for e in _ET}

def _m(pid, name, purpose, definition, transformation, execution, post_hoc, only_recorded, expected, tolerance, failure, confounds, valid, prov):
    return dict(id=pid, name=name, purpose=purpose, definition=definition, transformation=transformation, execution=execution,
                post_hoc=post_hoc, only_recorded_modified=only_recorded, expected=expected, tolerance=tolerance, failure_condition=failure,
                confounds=confounds, valid_for=valid, provenance_record=prov)

_PR = "PerturbationRecord(pid, params, seed, input_digest, output_digest, mode, execution_required, applicable, reason)"
PERTURBATION_MATRIX = {
 "P1": _m("P1", "relevant-evidence deletion", "Does assurance drop when the only evidence for a changed unit (or channel) is removed?",
    "Delete the clean SAME inputs that are sole reachers of one changed unit (or sole capturers of one channel).",
    "inputs -= sole reachers; recomputed from recorded parts, no execution.", False, True, True,
    "risk non-decreasing, or abstention (NDO -> INSUFFICIENT counts as pass)", "risk drop <= 1e-6", "risk decreases and decision is not an abstention",
    "deletion response is a function of the same recorded evidence and may be redundant with mu_min; N/A if nothing is deletable",
    _v(static_coverage="valid", repeat_runs="valid", observations="valid", provenance="partial", integrity="n/a", environment="n/a"), _PR),
 "P2": _m("P2", "irrelevant augmentation", "Is added evidence about unchanged code (quantity) credited as information?",
    "Add k inputs whose hits lie only on unchanged lines.",
    "POST-HOC variant: synthetic recorded inputs appended (hits off changed units, fresh fingerprints). EXECUTION variant (new runs via the V7-B engine) requires the collector.",
    True, True, True, "risk and decision unchanged", "|delta| <= 0.02, verdict equal", "risk moves more than tol or the verdict changes",
    "synthetic inputs are not real runs; fresh fingerprints inflate n_eff/n_same, which is the quantity trap being tested",
    _v(static_coverage="valid", repeat_runs="valid", observations="valid", provenance="valid"), _PR),
 "P3": _m("P3", "duplicate augmentation", "Is repeating the same evidence credited as independent evidence?",
    "Copy recorded inputs k times (same fingerprint, hits, provenance) with duplicate_of set.", "inputs += copies; no execution.",
    False, True, True, "risk and decision unchanged", "|delta| <= 0.02, verdict equal", "risk moves more than tol or the verdict changes",
    "a predictor reading raw len(inputs) (not the profile) is penalised by design",
    _v(static_coverage="valid", repeat_runs="valid", observations="valid", provenance="valid"), _PR),
 "P4": _m("P4", "observation masking", "Does losing observation channels raise risk?",
    "Drop channel(s) from channels_present of every input; inputs left with no channel become degenerate with a common fingerprint; a CONFIRMED_DIFF input left with no channel becomes degenerate SAME.",
    "post-hoc on recorded observations. APPROXIMATION: fingerprints of partially masked inputs cannot be recomputed from a hash, so they are kept.",
    False, True, True, "risk non-decreasing, or abstention", "risk drop <= 1e-6", "risk decreases and decision is not an abstention",
    "synthetic missed divergences do not follow the natural error distribution (property tests only, never fitting); N/A if channel immaterial",
    _v(observations="valid", static_coverage="n/a", repeat_runs="n/a"), _PR),
 "P5": _m("P5", "reproducibility-budget degradation", "Does less reproducibility evidence raise risk?",
    "Halve n_repeat_runs of all inputs and mark a seeded fraction of SAME inputs non-deterministic.",
    "POST-HOC variant on recorded flags. EXECUTION variant = re-collection with smaller r_det/r_replay/k_alt (config), requires the collector.",
    True, True, True, "risk non-decreasing, or abstention", "risk drop <= 1e-6", "risk decreases and decision is not an abstention",
    "post-hoc flags do not show whether a real smaller budget would still find the same witness",
    _v(repeat_runs="valid", observations="partial"), _PR),
 "P6": _m("P6", "independent discriminating evidence", "Does an independent input that reveals a difference change the outcome?",
    "Add an input with outcome CONFIRMED_DIFF, independent provenance, hitting all changed units.",
    "POST-HOC variant: synthetic recorded witness. EXECUTION variant (a genuinely new run) requires the collector. The response comes from the decision function.",
    True, True, True, "decision becomes DIVERGENT_OBSERVABLE, or risk increases, or abstention", "none beyond the disjunction", "none of the three happens",
    "a synthetic witness tests wiring, not discovery power; N/A when already divergent",
    _v(observations="valid", provenance="valid", static_coverage="partial"), _PR),
 "P7": _m("P7", "provenance degradation", "Does untrusted or label-derived provenance fail to raise assurance?",
    "Set provenance_ok False (mode=untrusted) or provenance=label_derived (mode=label_derived) on a seeded fraction of inputs.", "flags only.",
    False, True, True, "risk non-decreasing, or abstention", "risk drop <= 1e-6", "risk decreases and decision is not an abstention",
    "V7-B has no provenance concept: the V7-B-style decision is insensitive by construction",
    _v(provenance="valid", observations="partial"), _PR),
 "P8": _m("P8", "integrity violation", "Is corrupted or unverifiable evidence rejected?",
    "Set integrity_ok False; variant=corrupt also removes half of the recorded hits (simulated corruption).",
    "flag (sbgv8.trust.check works on evidence directories, not records; the record-level proxy is integrity_ok).",
    False, True, True, "evidence rejected: integrity_ok=0 and decision INSUFFICIENT", "exact", "perturbed record still yields NDO or DIVERGENT",
    "record-level flag only; real forgery detection is tested in test_trust, not here", _v(integrity="valid"), _PR),
 "P9": _m("P9", "environment inconsistency", "Does an inconsistent environment fail to raise assurance?",
    "Set env_consistent False and tag env_id.", "flags only.", False, True, True,
    "risk non-decreasing, or abstention", "risk drop <= 1e-6", "risk decreases and decision is not an abstention", "none beyond N/A when already inconsistent",
    _v(environment="valid"), _PR),
}
assert tuple(PERTURBATION_MATRIX) == PERTURBATIONS


@dataclass
class PerturbationRecord:
    pid: str
    params: dict
    seed: int
    input_digest: str
    output_digest: str
    mode: str                  # "post_hoc" (recorded evidence only) | "post_hoc_synthetic" (synthetic recorded inputs; true variant needs execution)
    execution_required: bool   # True: the real-execution version needs the collector; this record is only the recorded-input approximation
    applicable: bool = True
    reason: str = ""
    def to_dict(self): return asdict(self)


def _rng(pid, seed, rec): return random.Random(f"{pid}|{seed}|{rec.digest()}")
def _clean(i): return i.outcome == "SAME" and i.deterministic and not i.lossy
def _units(r): return sorted({(s, l) for s in ("base", "variant") for l in r.changed_units.get(s, [])})
def _hit(i): return {(s, l) for s in ("base", "variant") for l in i.hits.get(s, [])}


def _p1(r, rng, p):
    cl = [i for i in r.inputs if _clean(i) and not i.duplicate_of]
    cands = []
    for u in _units(r):
        h = [i.input_id for i in cl if u in _hit(i)]
        if len(h) == 1: cands.append(("unit", u, h))
    for c in r.declared_channels:
        h = [i.input_id for i in cl if c in i.channels_present]
        if len(h) == 1: cands.append(("channel", c, h))
    if p.get("kind"): cands = [c for c in cands if c[0] == p["kind"]]
    if not cands: return "no sole-reacher input to delete"
    kind, target, ids = rng.choice(cands)
    p["deleted"], p["target"] = ids, [kind, list(target) if kind == "unit" else target]
    r.inputs = [i for i in r.inputs if i.input_id not in ids]


def _p2(r, rng, p):
    if not any(_clean(i) for i in r.inputs): return "no clean SAME input: added inputs would be the first evidence, not irrelevant"
    k, ch = p.setdefault("k", 2), r.declared_channels
    off = sorted({l for i in r.inputs for s in ("base", "variant") for l in i.hits.get(s, [])} - {l for _, l in _units(r)})
    reps = max([i.n_repeat_runs for i in r.inputs] + [0])
    for j in range(k):
        line = off[j % len(off)] if off else 10**6 + j
        r.inputs.append(InputEvidence(f"p2_irr_{j}", "SAME", n_repeat_runs=reps, provenance="generator:p2_irrelevant",
                                      obs_fingerprint=hashlib.sha256(f"p2|{p.get('seed')}|{j}".encode()).hexdigest()[:16],
                                      channels_present=list(ch), hits={"base": [line], "variant": [line]}))


def _p3(r, rng, p):
    if not r.inputs: return "no inputs to duplicate"
    k, src = p.setdefault("k", 2), sorted(r.inputs, key=lambda i: i.input_id)
    for j in range(k):
        o = src[rng.randrange(len(src))]
        c = copy.deepcopy(o); c.input_id, c.duplicate_of = f"{o.input_id}#dup{j}", o.input_id
        r.inputs.append(c)


def _p4(r, rng, p):
    present = sorted({c for i in r.inputs for c in i.channels_present})
    chs = p.get("channels") or ([rng.choice(present)] if present else [])
    if not set(chs) & set(present): return "channel immaterial: no input captured it"
    p["channels"] = list(chs)
    for i in r.inputs:
        had = bool(i.channels_present)
        i.channels_present = [c for c in i.channels_present if c not in chs]
        if had and not i.channels_present:
            i.degenerate, i.obs_fingerprint = True, "masked-empty"
            if i.outcome == "CONFIRMED_DIFF": i.outcome = "SAME"


def _p5(r, rng, p):
    same = sorted((i for i in r.inputs if i.outcome == "SAME" and i.deterministic), key=lambda i: i.input_id)
    if not same: return "no deterministic SAME input to degrade"
    frac = p.setdefault("frac", 0.5)
    for i in rng.sample(same, max(1, round(frac * len(same)))): i.deterministic = False
    for i in r.inputs: i.n_repeat_runs //= 2


def _p6(r, rng, p):
    if any(i.outcome == "CONFIRMED_DIFF" for i in r.inputs): return "already divergent"
    r.inputs.append(InputEvidence("p6_witness", "CONFIRMED_DIFF", provenance="generator:p6_independent", n_repeat_runs=1,
                                  obs_fingerprint="p6-diff", channels_present=["outcome"],
                                  hits={s: list(r.changed_units.get(s, [])) for s in ("base", "variant")}))


def _p7(r, rng, p):
    if not r.inputs: return "no inputs"
    mode, frac = p.setdefault("mode", "label_derived"), p.setdefault("frac", 1.0)
    for i in rng.sample(sorted(r.inputs, key=lambda i: i.input_id), max(1, round(frac * len(r.inputs)))):
        if mode == "label_derived": i.provenance = "label_derived"
        else: i.provenance_ok = False


def _p8(r, rng, p):
    if not r.integrity_ok: return "integrity already violated"
    r.integrity_ok = False
    if p.setdefault("variant", "flag") == "corrupt":
        for i in r.inputs:
            for s in ("base", "variant"): i.hits[s] = i.hits.get(s, [])[::2]


def _p9(r, rng, p):
    if not r.env_consistent: return "environment already inconsistent"
    r.env_consistent, r.env_id = False, r.env_id + "|inconsistent"

_FN = {"P1": _p1, "P2": _p2, "P3": _p3, "P4": _p4, "P5": _p5, "P6": _p6, "P7": _p7, "P8": _p8, "P9": _p9}


def apply(rec, pid, seed=0, **params):
    """-> (new_record, PerturbationRecord). Not applicable -> unchanged copy with applicable=False and a reason."""
    if pid not in _FN: raise KeyError(pid)
    r, p = copy.deepcopy(rec), dict(params, seed=seed)
    reason = _FN[pid](r, _rng(pid, seed, rec), p)
    if reason: r = copy.deepcopy(rec)
    M = PERTURBATION_MATRIX[pid]
    mode = "post_hoc_synthetic" if pid in ("P2", "P6") else "post_hoc"
    return r, PerturbationRecord(pid, json.loads(json.dumps(p, default=list)), seed, rec.digest(), r.digest(), mode,
                                 bool(M["execution"]), reason is None, reason or "")
