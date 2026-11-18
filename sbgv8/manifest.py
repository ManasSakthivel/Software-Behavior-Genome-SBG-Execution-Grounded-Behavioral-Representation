"""V8 dataset manifest: data model, validation, JSONL/CSV IO, deterministic hashing, development-manifest builder.
Honest scope: the development manifest is DEVELOPMENT, design-exposed, not independent. Labels in it are Phase 2
generator/declared-test labels, never adjudicated labels."""
from __future__ import annotations
import csv, dataclasses, hashlib, json, os
from dataclasses import dataclass, field
from typing import Optional

MANIFEST_VERSION = "v8.manifest.1"
SPLITS = ("development", "calibration", "evaluation", "holdout")
OUTCOME_CLASSES = ("confirmed_divergence", "no_divergence_found_within_budget", "unresolved", "not_adjudicated", "sealed")
DEV_STATUS = "DEVELOPMENT, design-exposed, not independent"
FAMILY_RULE_DEV = "arm_prefix_v1"
FAMILY_RULE_DEV_DOC = ("family = source arm taken from the pair_id prefix before ':' (quixbugs and quixbugs_neg -> quixbugs; "
                       "synthetic -> synthetic; bugsinpy_units -> bugsinpy). Uses only pair_id/project identity; "
                       "never the truth label, verdict, generator-label column or the 'dataset' column (which encodes labels).")
REQUIRED = ("project", "family", "family_rule", "pair_id", "split", "provenance", "outcome_class")
DEV_CSV = "results/v7b_phase2_summary/p2_e3_20261118_092700/processed/dev_pairs_per_system.csv"

@dataclass
class ManifestRow:
    project: str
    family: str
    family_rule: str                      # rule id that derived `family` (label-independent)
    pair_id: str
    split: str = "development"
    version_info: dict = field(default_factory=dict)         # base/variant commit or version ids
    change_meta: dict = field(default_factory=dict)          # entry point, changed files, kind (never commit text as feature)
    observation_boundary: dict = field(default_factory=dict) # channels counted
    adjudication_budget: dict = field(default_factory=dict)  # frozen budget b
    outcome_class: str = "not_adjudicated"
    y: Optional[int] = None               # label (dev: generator label; Phase 3: adjudicated). Must be None for holdout rows
    label_source: str = ""
    provenance: dict = field(default_factory=dict)
    include: bool = True
    reasons: list = field(default_factory=list)              # inclusion/exclusion reasons
    status: str = ""

    def to_dict(self): return dataclasses.asdict(self)
    def digest(self):
        return hashlib.sha256(json.dumps(self.to_dict(), sort_keys=True).encode()).hexdigest()

def manifest_hash(rows):
    """Order-independent sha256 over row digests (sorted by pair_id)."""
    h = hashlib.sha256()
    for r in sorted(rows, key=lambda r: r.pair_id): h.update(r.digest().encode())
    return h.hexdigest()

def validate(rows, raise_on_error=False):
    """Return list of issue strings (empty = valid)."""
    iss, seen, proj_split, proj_fam = [], set(), {}, {}
    for r in rows:
        for f in REQUIRED:
            if getattr(r, f) in (None, "", {}, []): iss.append(f"{r.pair_id!r}: missing {f}")
        if r.split not in SPLITS: iss.append(f"{r.pair_id!r}: bad split {r.split!r}")
        if r.outcome_class not in OUTCOME_CLASSES: iss.append(f"{r.pair_id!r}: bad outcome_class {r.outcome_class!r}")
        if r.pair_id in seen: iss.append(f"duplicate pair_id {r.pair_id!r}")
        seen.add(r.pair_id)
        proj_split.setdefault(r.project, set()).add(r.split)
        proj_fam.setdefault(r.project, set()).add((r.family, r.family_rule))
        if r.split == "holdout" and (r.y is not None or r.label_source or r.outcome_class not in ("sealed", "not_adjudicated")):
            iss.append(f"{r.pair_id!r}: holdout row carries label information")
        if not r.include and not r.reasons: iss.append(f"{r.pair_id!r}: excluded without reason")
        if r.y not in (None, 0, 1): iss.append(f"{r.pair_id!r}: y must be 0/1/None")
    for p, s in sorted(proj_split.items()):
        if len(s) > 1: iss.append(f"project {p!r} in several splits {sorted(s)}")
    for p, f in sorted(proj_fam.items()):
        if len(f) > 1: iss.append(f"project {p!r} has several family derivations {sorted(f)}")
    if raise_on_error and iss: raise ValueError("; ".join(iss[:10]))
    return iss

_JSON_COLS = ("version_info", "change_meta", "observation_boundary", "adjudication_budget", "provenance", "reasons")

def write_jsonl(rows, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        for r in sorted(rows, key=lambda r: r.pair_id): f.write(json.dumps(r.to_dict(), sort_keys=True) + "\n")

def read_jsonl(path):
    with open(path) as f: return [ManifestRow(**json.loads(l)) for l in f if l.strip()]

def write_csv(rows, path):
    names = [f.name for f in dataclasses.fields(ManifestRow)]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, names); w.writeheader()
        for r in sorted(rows, key=lambda r: r.pair_id):
            d = r.to_dict()
            for c in _JSON_COLS: d[c] = json.dumps(d[c], sort_keys=True)
            w.writerow(d)

def read_csv(path):
    out = []
    with open(path, newline="") as f:
        for d in csv.DictReader(f):
            for c in _JSON_COLS: d[c] = json.loads(d[c])
            d["y"] = None if d["y"] == "" else int(d["y"])
            d["include"] = d["include"] == "True"
            out.append(ManifestRow(**d))
    return out

def derive_family_dev(pair_id):
    """Label-independent family rule arm_prefix_v1 (see FAMILY_RULE_DEV_DOC)."""
    pre = pair_id.split(":", 1)[0]
    return {"quixbugs": "quixbugs", "quixbugs_neg": "quixbugs", "synthetic": "synthetic", "bugsinpy_units": "bugsinpy"}.get(pre, "unknown_" + pre)

def _row_from_dev(pair_id, project, y, truth, src):
    return ManifestRow(
        project=project, family=derive_family_dev(pair_id), family_rule=FAMILY_RULE_DEV, pair_id=pair_id, split="development",
        version_info={"note": "not recorded in Phase 2 summary"}, change_meta={"arm_prefix": pair_id.split(":", 1)[0]},
        observation_boundary={"channels": ["outcome", "exception", "side_effect", "api"], "note": "declared V7-B default"},
        adjudication_budget={"note": "none: development labels are not adjudicated"},
        outcome_class="not_adjudicated", y=y, label_source="phase2_dev_generator_label",
        provenance={"source": src, "phase2_truth": truth}, include=y is not None,
        reasons=[] if y is not None else [f"unlabelled/suspect in Phase 2 ({truth}); kept out of risk estimation"], status=DEV_STATUS)

def build_dev_manifest(records_path="datasets/v8/dev_records.jsonl", csv_path=DEV_CSV):
    """Prefer dev_records.jsonl (EvidenceRecord JSON, one per line); else the Phase 2 per-system CSV (one row per pair, system B1)."""
    if os.path.exists(records_path):
        rows = []
        for l in open(records_path):
            if not l.strip(): continue
            d = json.loads(l)
            rows.append(_row_from_dev(d["pair_id"], d["project"], d.get("y"), (d.get("meta") or {}).get("truth", ""), records_path))
        return sorted(rows, key=lambda r: r.pair_id)
    ymap = {"DIV": 1, "NO_OBS_DIFF": 0}
    with open(csv_path, newline="") as f:
        rows = [_row_from_dev(d["pair_id"], d["project"], ymap.get(d["truth"]), d["truth"], csv_path)
                for d in csv.DictReader(f) if d["system"] == "B1"]
    return sorted(rows, key=lambda r: r.pair_id)

def cli_register(sp):
    p = sp.add_parser("manifest-dev", help="build+validate datasets/v8/DEV_MANIFEST.jsonl (development only)")
    p.add_argument("--out", default="datasets/v8/DEV_MANIFEST.jsonl")
    p.set_defaults(func=lambda a: print(_cli(a.out)))

def _cli(out):
    rows = build_dev_manifest(); write_jsonl(rows, out)
    return json.dumps({"rows": len(rows), "issues": validate(rows), "hash": manifest_hash(rows), "status": DEV_STATUS})
