"""d4_sets.py -- registry of the analysis sets used by D4 (shared by all d4_* scripts).

Status labels:
  PRE-REGISTERED   : set/statistic defined in SBG/docs/current/PHASE2_PREREGISTRATION.md s5/s6
                     (ALL = every pair in the frozen manifest, unevaluable scored 0;
                      EVALUABLE/VALID = both sides executed; cluster = program/bug).
  POST-HOC         : defined after external scores were seen (v8 harness rescore, SP-2 exclusion,
                     contamination / invalid-negative exclusions, project clustering, ...).
"""
from d4_lib import load_corpora

PRE = "PRE-REGISTERED"
POST = "POST-HOC EXPLORATORY"


def _not(kind):
    return lambda r: r["kind"] != kind


def contaminated(recs):
    """Pairs whose base unit has non-zero v8 self-distance (cold-start contamination)."""
    return {r["base_path"] for r in recs if r["self_dist8"] not in (None, 0, 0.0)}


def invalid_sp2_ids(audit):
    ids = set()
    for corp in audit["corpora"].values():
        for t in corp.values():
            for p in t.get("pairs", []):
                ids.add(p["pair_id"])
    return ids


SET_DEFS = [
    # id, corpus, source, filter-name, impute, status, description
    ("BP-v6-EVAL", "bugsinpy", "s6", "ev6", None, PRE, "BugsInPy v6 protocol, evaluable (committed BUGSINPY_output_free_v6.json VALID: 140)"),
    ("BP-v7-ALL", "bugsinpy", "s7", "all", 0.0, PRE, "BugsInPy v7, ALL 200 pairs, unevaluable scored 0 (prereg ALL set)"),
    ("BP-v7-EVAL", "bugsinpy", "s7", "ev7", None, PRE, "BugsInPy v7 EVALUABLE=VALID (147), prereg primary set (committed 0.409917)"),
    ("BP-v8-EVAL", "bugsinpy", "s8", "ev8", None, POST, "BugsInPy v8 corrected-harness rescore, same 147 pairs (EXTERNAL_RESCORE_V8, 0.4159)"),
    ("BP-v8-exSP2", "bugsinpy", "s8", "ev8_noSP2", None, POST, "v8 rescore excluding all SP-2 negatives (107 pairs) = reported 0.497"),
    ("BP-v7-exSP2", "bugsinpy", "s7", "ev7_noSP2", None, POST, "v7 committed scores excluding SP-2 (107 pairs; A3 0.4715)"),
    ("BP-v8-exInvalidSP2", "bugsinpy", "s8", "ev8_noInvalid", None, POST, "v8 rescore excluding the 7 statically invalid SP-2 negatives (140 pairs)"),
    ("BP-v8-exContam", "bugsinpy", "s8", "ev8_noContam", None, POST, "v8 rescore excluding all pairs of the 3 cold-start-contaminated base units"),
    ("BP-v8-exSP2-exContam", "bugsinpy", "s8", "ev8_noSP2_noContam", None, POST, "v8 ex-SP-2 and ex contaminated bases"),
    ("QC-v7-ALL", "quixbugs_canonical", "s7", "ev7", None, PRE, "QuixBugs canonical v7 (all 152 evaluated; committed 0.387723)"),
    ("QC-v8-EVAL", "quixbugs_canonical", "s8", "ev8", None, POST, "QuixBugs canonical v8 rescore (151 evaluated; 0.3842)"),
    ("QC-v8-exSP2", "quixbugs_canonical", "s8", "ev8_noSP2", None, POST, "v8 rescore excluding SP-2 (111 pairs) = reported 0.444"),
    ("QC-v7-exSP2", "quixbugs_canonical", "s7", "ev7_noSP2", None, POST, "v7 committed scores excluding SP-2 (112 pairs; 0.4507)"),
    ("QC-v8-exContam", "quixbugs_canonical", "s8", "ev8_noContam", None, POST, "v8 rescore excluding pairs of the 1 contaminated base"),
    ("QC-v8-exSP2-exContam", "quixbugs_canonical", "s8", "ev8_noSP2_noContam", None, POST, "v8 ex-SP-2 and ex contaminated base"),
    ("QD-v7-ALL", "quixbugs_declared", "s7", "all", 0.0, PRE, "QuixBugs declared-input regime (secondary prereg), ALL 152, unevaluable scored 0"),
    ("QD-v7-EVAL", "quixbugs_declared", "s7", "ev7", None, PRE, "QuixBugs declared-input regime, EVALUABLE (99)"),
    ("QD-v7-exSP2", "quixbugs_declared", "s7", "ev7_noSP2", None, POST, "declared regime evaluable excluding SP-2 (72)"),
]


def select(recs, flt, invalid_ids=None):
    cont = contaminated(recs)
    f = {
        "all": lambda r: True,
        "ev6": lambda r: bool(r["ev6"]),
        "ev7": lambda r: r["ev7"],
        "ev8": lambda r: bool(r["ev8"]),
        "ev7_noSP2": lambda r: r["ev7"] and r["kind"] != "SP-2",
        "ev8_noSP2": lambda r: bool(r["ev8"]) and r["kind"] != "SP-2",
        "ev8_noInvalid": lambda r: bool(r["ev8"]) and r["pair_id"] not in (invalid_ids or ()),
        "ev8_noContam": lambda r: bool(r["ev8"]) and r["base_path"] not in cont,
        "ev8_noSP2_noContam": lambda r: bool(r["ev8"]) and r["kind"] != "SP-2" and r["base_path"] not in cont,
    }[flt]
    return [r for r in recs if f(r)]


def get_sets(C, audit):
    inv = invalid_sp2_ids(audit)
    out = {}
    for sid, corpus, src, flt, imp, status, desc in SET_DEFS:
        out[sid] = dict(id=sid, corpus=corpus, src=src, flt=flt, impute=0.0 if imp is None else imp,
                        status=status, desc=desc, recs=select(C[corpus], flt, inv))
    return out
