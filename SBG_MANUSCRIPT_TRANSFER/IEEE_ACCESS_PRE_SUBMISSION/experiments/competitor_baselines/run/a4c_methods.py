"""A4C method registry: families (pre-declared Holm family of plan §3), configuration grids, labels (REPRODUCED/ADAPTED), privileged flags."""
from __future__ import annotations

X3 = ["exception_fraction", "call_count", "coverage_size"]
XE = ["n_functions", "n_events", "trace_len_mean"]
FEATS = {"E": ["edit"], "X": X3, "EX": ["edit"] + X3, "EXx": ["edit"] + X3 + XE, "Xx": X3 + XE}
MODEL_NAMES = {"LR_E": "E", "LR_X": "X", "LR_EX": "EX", "LR_EXx": "EXx", "LR_Xx": "Xx"}
INC_X = ["sbg_v5", "sbg_state", "sbg_v3", "sbg_temporal", "valuespectra*", "traceseq_rename_robust*", "pathspectra*", "output_indep|frac40"]
SBG_REFS = ["sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state"]
STATIC_OWN = ["tok_lev_raw", "tok_lev_alpha", "astseq_lev_types", "astseq_lev_alpha", "tfidf2", "tfidf3", "bytecode_lev"]
FOREST_SPECS = [f"forest|{k}_d{d}|{fs}" for fs in ("EXx", "Xx") for k, ds in (("DT", (2, 3, 4)), ("RF", (3, 4, 6))) for d in ds]


def families():
    import b04_valuespectra
    import b05_pathspectra
    import b05_traceseq
    ts = b05_traceseq.config_names()
    return {
        "edit_fwd": ["edit"],
        "static_token": ["static_token"], "static_ast": ["static_ast"],
        "static_own*": [f"static|{c}" for c in STATIC_OWN],
        "tce_analogue*": ["static|tce_ast", "static|tce_bytecode"],
        "execstat_single*": ["exception_fraction", "call_count", "coverage_size", "n_functions", "n_events", "trace_len_mean"],
        "LR_EX": ["LR_EX"], "LR_X": ["LR_X"], "LR_EXx*": ["LR_EXx", "LR_Xx"],
        "forest_nonlinear*": list(FOREST_SPECS),
        "sbg_state": ["sbg_state"], "sbg_v3": ["sbg_v3"], "sbg_temporal": ["sbg_temporal"],
        "valuespectra*": b04_valuespectra.config_names(),
        "traceseq_rename_robust*": [c for c in ts if c.split("|")[2] in ("entry", "full")],
        "traceseq_naive*": [c for c in ts if c.split("|")[2] == "raw"],
        "birthmark_k*": [c for c in ts if c.split("|")[3].startswith("kgram")],
        "pathspectra*": b05_pathspectra.config_names(),
        "output_indep_frac40": ["output_indep|frac40"],
    }


DIAG = {
    "edit_rev": ["edit_rev"],
    "oracle_ceiling": ["oracle|frac11", "oracle|any11", "oracle|frac11_excmsg", "changeguard_cmp|frac11", "changeguard_cmp|any11"],
    "output_indep_variants": ["output_indep|any40", "output_indep|frac40_excmsg", "output_indep|frac11", "output_indep|any11"]
                             + [f"output_indep|{m}_k{k}" for k in (1, 2, 4, 8, 16, 32) for m in ("any", "frac")],
    "sbg_v6": ["sbg_v6", "sbg_state_v6"],
}
FAMILY_CLASS = {"edit_fwd": "A", "static_token": "A", "static_ast": "A", "static_own*": "A", "tce_analogue*": "A", "execstat_single*": "A", "LR_EX": "A", "LR_X": "A",
                "LR_EXx*": "A", "forest_nonlinear*": "A", "sbg_state": "ref", "sbg_v3": "ref", "sbg_temporal": "ref", "valuespectra*": "B", "traceseq_rename_robust*": "B",
                "traceseq_naive*": "B", "birthmark_k*": "A/B", "pathspectra*": "B", "output_indep_frac40": "B"}
REPRODUCED_KEYS = {"edit", "edit_rev", "static_token", "static_ast", "exception_fraction", "call_count", "coverage_size", "n_functions", "LR_E", "LR_X", "LR_EX",
                   "sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state", "sbg_v6", "sbg_state_v6"}
HEADLINE_FAMILY_SBG = "sbg_v5"


def privileged(key: str) -> bool:
    if key.startswith(("output_indep", "oracle", "changeguard_cmp")):
        return True
    if key.startswith("valuespectra|"):
        return key.split("|")[1] in ("entry_exit", "exit")
    if key.startswith("INC|"):
        return "output_indep" in key
    return False


def label_of(key: str) -> str:
    return "REPRODUCED" if key in REPRODUCED_KEYS else "ADAPTED"


def all_config_keys():
    keys = ["sbg_v5"]
    for cs in families().values():
        keys += cs
    keys += [c for cs in DIAG.values() for c in cs]
    return list(dict.fromkeys(keys))


def family_of():
    out = {}
    for f, cs in families().items():
        for c in cs:
            out.setdefault(c, f)
    for f, cs in DIAG.items():
        for c in cs:
            out.setdefault(c, f"diag:{f}")
    return out


def safe(key: str) -> str:
    """file-system-safe method name"""
    return key.replace("|", "__").replace("*", "").replace("+", "_plus_").replace("/", "_")
