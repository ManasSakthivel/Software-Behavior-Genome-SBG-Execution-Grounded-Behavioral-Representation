"""Shared V8 schemas. SINGLE SOURCE OF TRUTH for interfaces between collection, profile, perturbation, calibration, evaluation.
Changing a name here requires coordinating every module. Pure data; no I/O side effects beyond to_json/from_json."""
from __future__ import annotations
import dataclasses, hashlib, json
from dataclasses import dataclass, field
from typing import Optional

SCHEMA_VERSION = "v8.0"
VERDICTS = ("DIVERGENT_OBSERVABLE", "INSUFFICIENT", "NO_DIVERGENCE_OBSERVED")
# Adjudicated outcome Y: 1 confirmed divergence within scope; 0 no divergence found within budget; None unresolved/unlabelled.
CHANNELS = ("outcome", "exception", "side_effect", "api")

@dataclass
class InputEvidence:
    input_id: str
    outcome: str                      # SAME | CONFIRMED_DIFF | QUARANTINED | NO_RUN | ... (V7-B InputEv.outcome)
    lossy: bool = False
    degenerate: bool = False
    deterministic: bool = True        # deterministic-confirmed (not quarantined / flaky)
    n_repeat_runs: int = 0            # recorded repeat+replay+alt runs (reproducibility evidence)
    provenance: str = "declared"      # declared | generator:<name> | llm:<family> | developer_test | label_derived | unknown
    provenance_ok: bool = True        # provenance record present and trusted
    obs_fingerprint: str = ""         # hash of canonical variant observation (identical observations share it)
    channels_present: list = field(default_factory=list)   # observation channels actually captured for this input
    hits: dict = field(default_factory=lambda: {"base": [], "variant": []})        # executed changed-or-not lines per side
    branches: dict = field(default_factory=lambda: {"base": {}, "variant": {}})    # {side: {branch_key: [directions]}}
    duplicate_of: Optional[str] = None  # set by perturbation P3 to mark a duplicated (non-independent) copy

@dataclass
class EvidenceRecord:
    pair_id: str
    project: str
    family: str = "unknown"
    split: str = "development"        # development | calibration | evaluation | holdout
    y: Optional[int] = None           # adjudicated outcome (1/0/None); NEVER read by profile/perturbation code
    v7b_verdict: str = ""             # historical V7-B verdict (value), for baselines only
    v7b_level: Optional[str] = None
    inputs: list = field(default_factory=list)          # list[InputEvidence]
    changed_units: dict = field(default_factory=lambda: {"base": [], "variant": []})   # changed executable lines per side
    static_branches: dict = field(default_factory=lambda: {"base": 0, "variant": 0})   # branch instruction count on changed lines
    declared_channels: list = field(default_factory=lambda: list(CHANNELS))
    env_id: str = ""
    env_consistent: bool = True
    integrity_ok: bool = True         # evidence verification result (verify / V8 trust check)
    blockers: list = field(default_factory=list)        # V7-B blocker codes (hard INSUFFICIENT reasons)
    config: dict = field(default_factory=dict)          # r_det, r_replay, k_alt, s2_branch_floor
    meta: dict = field(default_factory=dict)            # free-form (arm, source paths, run ids); never used as a feature

    def to_json(self):
        return json.dumps(dataclasses.asdict(self), sort_keys=True)

    @staticmethod
    def from_json(s):
        d = json.loads(s) if isinstance(s, str) else s
        d["inputs"] = [InputEvidence(**i) for i in d.get("inputs", [])]
        return EvidenceRecord(**d)

    def digest(self):
        d = dataclasses.asdict(self); d.pop("y", None); d.pop("meta", None)
        return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()

# ---- Feature names (profile.py must produce exactly these keys; groups are used by baselines/ablations) ----
FEATURES = [
    "act_frac",          # D1 changed-unit activation fraction (deterministic clean SAME inputs)
    "branch_cov_min",    # D1 min over sides of changed-line branch-direction coverage
    "mu_min",            # multiplicity: min over changed units of #distinct-observation SAME inputs hitting it
    "mu_mean",           # multiplicity: mean of the same
    "n_same",            # number of clean deterministic SAME inputs
    "n_rep",             # total recorded repeat/replay/alt runs backing the SAME inputs (repetition)
    "obs_react",         # D2 PROXY of observable influence: fraction of changed units hit by an input with non-degenerate, non-lossy observation
    "n_eff",             # D5 distinct observation fingerprints among clean SAME inputs
    "n_eff_prov",        # D5/D6 distinct (fingerprint, provenance class) after collapsing same-provenance duplicates
    "repro_frac",        # D4 fraction of inputs deterministic-confirmed
    "lossy_frac",        # D3 fraction of inputs lossy or degenerate
    "chan_complete",     # D3 mean fraction of declared channels captured
    "prov_ok",           # D6 1.0 if all inputs have trusted provenance and none is label_derived, else 0.0
    "integrity_ok",      # D8 1.0/0.0
    "env_ok",            # D7 1.0/0.0
]
FEATURE_SETS = {
    "cov_only":        ["act_frac", "branch_cov_min"],
    "cov_rep":         ["act_frac", "branch_cov_min", "n_rep"],
    "cov_mult":        ["act_frac", "branch_cov_min", "mu_min", "mu_mean", "n_same"],
    "cov_act":         ["act_frac", "branch_cov_min", "act_frac"],          # activation is already in cov; kept for symmetry, dedup by loader
    "cov_infl":        ["act_frac", "branch_cov_min", "obs_react"],
    "cov_prov":        ["act_frac", "branch_cov_min", "prov_ok", "integrity_ok", "env_ok"],
    "full_profile":    list(FEATURES),
}
PERTURBATIONS = ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9")
ERS_FEATURES = [f"ers_{p}_delta" for p in PERTURBATIONS]   # response features (ers.ers_vector); full_cec = full_profile + ERS_FEATURES
