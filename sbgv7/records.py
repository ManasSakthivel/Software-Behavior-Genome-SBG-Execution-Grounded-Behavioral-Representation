"""Evidence records (content-addressed ids) and the hash-chained JSONL log.
Evidence classes per spec 8: Run/Observation=observation, Witness/SufficiencyRecord/ProgramVersion=derived,
Verdict=derived. Prohibited-as-outcome words are not representable: Verdict.value is a closed enum."""
import hashlib, json
from dataclasses import dataclass, field, asdict

VERDICTS = ("DIVERGENT_OBSERVABLE", "INSUFFICIENT", "NO_DIVERGENCE_OBSERVED")
REASON_CODES = ("import_error unsupported_signature ambiguous_entry alignment_failed unmodelled_change sandbox_failure "
                "unsafe_program flaky_witness env_sensitive nondeterministic resource_limit capture_truncated "
                "blind_spot_dominant no_inputs unobservable_outcome changed_region_not_activated budget_exhausted_s0 "
                "tool_error").split()
EVIDENCE_CLASSES = ("observation", "derived", "inferred", "proof")


def canon_json(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def content_id(kind, payload):
    return kind[:3].lower() + "_" + hashlib.sha256(canon_json([kind, payload]).encode()).hexdigest()[:24]


def sha(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode()).hexdigest()


class InvariantError(ValueError, AssertionError):
    """A record invariant was violated. Explicit raise (not `assert`) so `python -O` cannot disable it (MB-04)."""


def _inv(ok, msg):
    if not ok: raise InvariantError(msg)


@dataclass
class Rec:
    kind: str = ""
    id: str = ""
    evidence_class: str = "observation"
    status: str | None = None  # missing | invalid | uncertain
    refs: list = field(default_factory=list)  # ids this record is derived from
    body: dict = field(default_factory=dict)  # content (hashed into id unless listed in meta)
    meta: dict = field(default_factory=dict)  # non-identity data (timings); stored, not hashed into id

    def __post_init__(self):
        _inv(self.evidence_class in EVIDENCE_CLASSES, f"unknown evidence class {self.evidence_class!r}")
        if not self.id:
            self.id = content_id(self.kind, [self.evidence_class, self.refs, self.body])


SRC_CAP, INPUT_CAP = 1 << 20, 256 << 10  # evidence size caps; over cap the item is recorded as omitted and the verdict is not recomputable


def ProgramVersion(role, src_bytes, entry):
    # source text lives in meta (not in the id, but inside the chain hash) so a verdict can be recomputed from the log alone
    meta = {"src": src_bytes.decode("utf-8", "surrogateescape")} if len(src_bytes) <= SRC_CAP else {"src_omitted": len(src_bytes)}
    return Rec("ProgramVersion", evidence_class="derived", body={"role": role, "sha256": sha(src_bytes), "entry": entry}, meta=meta)


def pack_inputs(inputs):
    return [{"id": i["id"], "args": i["args"], "kwargs": i["kwargs"]} if len(canon_json([i["args"], i["kwargs"]])) <= INPUT_CAP
            else {"id": i["id"], "omitted": len(canon_json([i["args"], i["kwargs"]])), "sha": sha(canon_json([i["args"], i["kwargs"]]))} for i in inputs]


def EvidencePackage(body):
    """Everything a verifier needs besides runs/observations/versions: H/config, env, policy, inputs, rows, regions, stop reason."""
    return Rec("EvidencePackage", evidence_class="derived", body=body)


def Run(version_id, input_hash, run_kind, idx, harness_decl_id, obs_id, summary, meta, rid_extra=""):
    r = Rec("Run", refs=[version_id] + ([obs_id] if obs_id else []), body={"input_hash": input_hash, "run_kind": run_kind, "idx": idx,
            "harness_decl_id": harness_decl_id, "summary": summary, "x": rid_extra}, meta=meta)
    # run identity is its slot (version, input, kind, idx, H), not its outcome: stable across invocations
    r.id = content_id("Run", [version_id, input_hash, run_kind, idx, harness_decl_id, rid_extra])
    return r


def Observation(obs):
    return Rec("Observation", body={k: v for k, v in obs.items() if k not in ("hits", "branches")})


def Witness(pair, scope, input_hash, harness_decl_id, kinds, obs_old, obs_new, replay_set, env_id, sandbox_policy_id):
    return Rec("Witness", evidence_class="derived", refs=[obs_old, obs_new] + [r["run_id"] for r in replay_set],
               body=dict(pair=pair, scope=scope, input_hash=input_hash, harness_decl_id=harness_decl_id, kinds=kinds, obs_old=obs_old,
                         obs_new=obs_new, replay_set=replay_set, locus="unlocalised", env_id=env_id, sandbox_policy_id=sandbox_policy_id))


def SufficiencyRecord(refs, body):
    return Rec("SufficiencyRecord", evidence_class="derived", status="uncertain", refs=refs, body=body)


def Verdict(value, level, primary, secondary, refs, pair_id):
    _inv(value in VERDICTS, f"verdict value {value!r} is not one of {VERDICTS}")
    _inv((level is not None) == (value == "NO_DIVERGENCE_OBSERVED") and level in (None, "S1", "S2"), f"level {level!r} invalid for {value}")  # S0 only inside INSUFFICIENT; S3 disabled
    _inv((primary is not None) == (value == "INSUFFICIENT") and (primary is None or primary in REASON_CODES), f"primary {primary!r} invalid for {value}")
    _inv(all(c in REASON_CODES for c in secondary), f"unknown secondary reason code in {list(secondary)}")
    return Rec("Verdict", evidence_class="derived", refs=refs, body=dict(value=value, level=level, primary=primary,
               secondary=sorted(secondary), pair_id=pair_id))


def merkle_root(ids):
    """Binary Merkle root over the SORTED, de-duplicated ids (order-independent); an odd node is promoted unchanged."""
    lvl = [sha(i) for i in sorted(set(ids))] or [sha("")]
    while len(lvl) > 1:
        lvl = [sha(lvl[i] + lvl[i + 1]) if i + 1 < len(lvl) else lvl[i] for i in range(0, len(lvl), 2)]
    return lvl[0]


class ChainError(Exception):
    pass


class EvidenceLog:
    def __init__(self, path):
        self.path, self.prev, self.n = path, "0" * 64, 0
        open(path, "x").close()  # MB-08: never truncate existing evidence (FileExistsError)

    def append(self, rec):
        d = asdict(rec)
        h = sha(self.prev + canon_json(d))
        with open(self.path, "a") as f:
            f.write(canon_json({"seq": self.n, "prev": self.prev, "rec": d, "hash": h}) + "\n")
        self.prev, self.n = h, self.n + 1
        return rec.id


def read_log(path):
    """Verify the chain and return records. Raises ChainError at the first broken link."""
    prev, out = "0" * 64, []
    for i, line in enumerate(open(path)):
        e = json.loads(line)
        if e["seq"] != i or e["prev"] != prev or e["hash"] != sha(prev + canon_json(e["rec"])):
            raise ChainError(f"chain broken at seq {i}")
        prev = e["hash"]; out.append(e["rec"])
    return out


def trace(path, record_id):
    """All records reachable from record_id via refs (verdict -> witness/sufficiency -> runs -> observations/versions)."""
    recs = {r["id"]: r for r in read_log(path)}
    if record_id not in recs: raise KeyError(record_id)
    seen, stack = {}, [record_id]
    while stack:
        i = stack.pop()
        if i in seen: continue
        if i not in recs: raise ChainError(f"dangling ref {i}")
        seen[i] = recs[i]; stack += recs[i]["refs"]
    return seen
