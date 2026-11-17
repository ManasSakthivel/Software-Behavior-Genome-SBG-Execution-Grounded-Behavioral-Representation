"""Glue: run both versions on the same inputs through sbgv7.isolation (fresh child per run), classify determinism /
replay, compute changed-region activation, then hand facts to decide(). Logs every step to the evidence log.
Reuses sbgv6.features.changed_lines (read-only import)."""
import dis, hashlib, json, os, sys
from dataclasses import dataclass, field

from sbgv6.features import changed_lines
from . import isolation, records as R
from .compare import compare
from .decide import Evidence, InputEv, decide

HARNESS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "harness.py")
MARK = "SBGV7RESULT:"
BRANCH_OPS = ("POP_JUMP_IF_FALSE", "POP_JUMP_IF_TRUE", "POP_JUMP_IF_NONE", "POP_JUMP_IF_NOT_NONE", "FOR_ITER", "SEND")


class Ineligible(Exception):
    pass


@dataclass
class RunOut:
    run_id: str
    obs: dict | None          # None for limit / non-call runs
    limit: str | None = None
    phase: str = "ok"
    msg: str = ""
    sandbox_ok: bool = True
    truncated: bool = False
    tampered: bool = False
    hits: set = field(default_factory=set)
    branches: dict = field(default_factory=dict)
    sig: list | None = None
    obs_id: str | None = None


class Ctx:
    def __init__(self, cfg, log, entry, base_path, var_path):
        self.cfg, self.log, self.entry, self.spent = cfg, log, entry, 0.0
        self.src = {"base": open(base_path, "rb").read(), "variant": open(var_path, "rb").read()}
        self.path = {"base": os.path.abspath(base_path), "variant": os.path.abspath(var_path)}
        self.caps = isolation.capabilities()
        self.env_id = R.content_id("Env", [sys.version, sys.platform, {k: v["state"] for k, v in self.caps.items() if isinstance(v, dict)}])
        self.policy_id = R.content_id("Policy", [R.sha(open(isolation.PROFILE, "rb").read()) if os.path.exists(isolation.PROFILE) else "",
                                                 {k: v["state"] for k, v in self.caps.items() if isinstance(v, dict)}])
        self.h_id = R.content_id("H", [cfg["harness"], R.sha(open(HARNESS, "rb").read())])
        self.vers = {}
        for s in self.src:
            pv = R.ProgramVersion(s, self.src[s], entry)
            self.vers[s] = log.append(pv)
        self.pair_id = R.content_id("Pair", [self.vers["base"], self.vers["variant"], entry, self.h_id])

    def run(self, side, inp, kind, idx, mode="call", ctl=None):
        c = self.cfg["budget"]["per_run"]
        h = R.sha(R.canon_json([inp["args"], inp["kwargs"]]))
        arg = json.dumps(dict(src=self.path[side], entry=self.entry, mode=mode, args=inp["args"], kwargs=inp["kwargs"], ctl=ctl))
        r = isolation.run_script(HARNESS, [arg], timeout_s=c["wall_s"], cpu_s=c["cpu_s"], mem_mb=c["rss_mib"], out_cap=4 << 20)
        self.spent += r.cpu_s
        out = RunOut("", None)
        out.sandbox_ok = r.status != "SANDBOX_UNAVAILABLE" and r.cleanup_verified and not r.orphans_found and "rlimit could not" not in r.detail
        out.truncated = r.stdout_truncated
        line = next((l for l in reversed(r.stdout.splitlines()) if l.startswith(MARK)), None)
        if r.status in ("TIMEOUT", "RESOURCE"):
            out.limit = r.detail
        elif line and not r.stdout_truncated:
            d = json.loads(line[len(MARK):])
            out.phase, out.msg = d["phase"], d.get("msg", "")
            out.truncated |= bool(d.get("stdout_trunc"))
            out.tampered, out.sig = d.get("tampered", False), d.get("sig")
            out.hits, out.branches = set(d.get("hits", [])), d.get("branches", {})
            if d["phase"] == "ok" and mode == "call": out.obs = d
        elif out.sandbox_ok and not r.stdout_truncated:  # hard exit/kill without a result line
            out.obs = {"t": "crashed", "signal": r.signal} if r.signal else {"t": "exited", "code": ["int", str(r.returncode)]}
            out.phase = "ok"
        obs_id = self.log.append(R.Observation(out.obs)) if out.obs else None
        summ = {"status": r.status, "detail": r.detail, "phase": out.phase, "limit": out.limit, "truncated": out.truncated,
                "sandbox_ok": out.sandbox_ok, "tampered": out.tampered, "n_hits": len(out.hits)}
        rec = R.Run(self.vers[side], h, kind, idx, self.h_id, obs_id, summ,
                    {"cpu_s": r.cpu_s, "wall_s": r.wall_s, "hits": sorted(out.hits)}, rid_extra=f"{mode}/{ctl}")
        out.run_id = self.log.append(rec)
        out.obs_id = obs_id
        return out


def _same(ctx, a, b):
    """Self-consistency / reproduction: equal under H (limit outcomes compare by kind)."""
    if a.obs is None or b.obs is None:
        return a.obs is None and b.obs is None and a.limit == b.limit
    return compare(a.obs, b.obs, ctx.cfg["harness"]).equal


def _exec_lines(src):
    def walk(c):
        yield from (l for _, _, l in c.co_lines() if l)
        for k in c.co_consts:
            if hasattr(k, "co_code"): yield from walk(k)
    return set(walk(compile(src, "<v>", "exec")))


def _static_branches(src, lines):
    """{'qualname:firstlineno:offset'} of branch instructions on `lines`."""
    out = set()
    def walk(c):
        for i in dis.get_instructions(c):
            if i.opname in BRANCH_OPS and i.positions and i.positions.lineno in lines:
                out.add(f"{c.co_qualname}:{c.co_firstlineno}:{i.offset}")
        for k in c.co_consts:
            if hasattr(k, "co_code"): walk(k)
    walk(compile(src, "<v>", "exec"))
    return out


def _sig_compatible(a, b):
    """Same names/kinds for base's parameters (a default may be added, not removed); extra variant params need defaults."""
    return len(b) >= len(a) and all(x[:2] == y[:2] and (y[2] or not x[2]) for x, y in zip(a, b)) and all(p[2] for p in b[len(a):])


def process_input(ctx, inp):
    """-> (InputEv, hits{side}, branches{side}, lossy) following spec 5 protocol."""
    cfg, h = ctx.cfg, ctx.cfg["harness"]
    rep = cfg["repeat"]
    ih = R.sha(R.canon_json([inp["args"], inp["kwargs"]]))
    runs = {"base": [], "variant": []}
    ev = InputEv(inp["id"], truncated=False, sandbox_ok=True)
    stat = []
    consistent = True
    for side in runs:  # step 1: r_det repeats, early stop at first disagreement
        runs[side].append(ctx.run(side, inp, "primary", 0))
        for k in range(1, rep["r_det"]):
            if runs[side][0].obs is None and runs[side][0].limit: break
            runs[side].append(ctx.run(side, inp, "repeat", k))
            if not _same(ctx, runs[side][0], runs[side][-1]):
                consistent = False; break
    allruns = runs["base"] + runs["variant"]
    ev.run_ids = tuple(r.run_id for r in allruns)
    ev.sandbox_ok = all(r.sandbox_ok for r in allruns)
    ev.truncated = any(r.truncated for r in allruns)
    for r in allruns:
        if r.phase in ("import_error", "entry_missing", "harness_error"):
            stat.append(("tool_error" if r.phase == "harness_error" else "import_error", f"{inp['id']}: {r.phase} in call run: {r.msg}"))
    hits = {s: set().union(*[r.hits for r in runs[s]]) for s in runs}
    br = {s: {} for s in runs}
    for s in runs:
        for r in runs[s]:
            for k, v in r.branches.items(): br[s].setdefault(k, set()).update(v)
    if stat or not ev.sandbox_ok:
        ev.outcome = "NO_RUN"
        return ev, hits, br, False, stat
    p = {s: runs[s][0] for s in runs}
    if not consistent:
        ev.outcome = "QUARANTINED"; return ev, hits, br, False, stat
    lim = [p[s].limit for s in p if p[s].obs is None]
    if lim:
        ev.outcome = "NO_RUN" if len(lim) == 2 else "LIMIT_ASYMMETRIC"; return ev, hits, br, False, stat
    cmp = compare(p["base"].obs, p["variant"].obs, h)
    if cmp.equal:
        ev.outcome, ev.lossy = "SAME", cmp.lossy
        o = p["base"].obs
        ev.degenerate = (o["t"] == "returned" and o["ret"] == ["none"] and not o["stdout"] and not o["files"] and not o["globals"]
                         and not o["args_changed"]) if "stdout" in o else False
        return ev, hits, br, cmp.lossy, stat
    # step 2: replay 5 fresh runs per side; confirmed iff all reproduce each side's primary and the versions still differ
    rs = {s: [ctx.run(s, inp, "replay", k) for k in range(rep["r_replay"])] for s in runs}
    ev.run_ids += tuple(r.run_id for s in rs for r in rs[s])
    ev.sandbox_ok &= all(r.sandbox_ok for s in rs for r in rs[s]); ev.truncated |= any(r.truncated for s in rs for r in rs[s])
    ok = sum(_same(ctx, p[s], r) for s in rs for r in rs[s])
    total = 2 * rep["r_replay"]
    if ok < total:  # intermittent (0<ok) or failed_reproduction (ok==0): both unconfirmed
        ev.outcome = "UNCONFIRMED_DIFF"; ev.repro = "intermittent" if ok else "failed_reproduction"
        return ev, hits, br, False, stat
    # step 4: control-sensitivity: k_alt alternate control settings, each side's own observation must be invariant
    alt = {s: [ctx.run(s, inp, "alt", k, ctl=k + 1) for k in range(rep["k_alt"])] for s in runs}
    ev.run_ids += tuple(r.run_id for s in alt for r in alt[s])
    if not all(_same(ctx, p[s], r) for s in alt for r in alt[s]):
        ev.outcome = "ENV_SENSITIVE_DIFF"; return ev, hits, br, False, stat
    replay_set = [{"run_id": r.run_id, "version": s, "observation": r.obs_id, "status": "reproduced"} for s in rs for r in rs[s]]
    w = R.Witness(ctx.pair_id, ctx.entry, ih, ctx.h_id, cmp.kinds, p["base"].obs_id, p["variant"].obs_id, replay_set, ctx.env_id, ctx.policy_id)
    w.refs += [p["base"].run_id, p["variant"].run_id] + [r.run_id for s in alt for r in alt[s]]
    ev.witness_id = ctx.log.append(w)
    ev.outcome = "CONFIRMED_DIFF"
    return ev, hits, br, False, stat


def compare_versions(base_path, var_path, entry, inputs, cfg, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    log = R.EvidenceLog(os.path.join(out_dir, "evidence.jsonl"))
    ctx = Ctx(cfg, log, entry, base_path, var_path)
    if ctx.src["base"] == ctx.src["variant"]:
        raise Ineligible("ineligible:identical (source bytes identical; no verdict is issued)")
    st = []  # static blockers (B1, B2)
    sigs = {}
    probe_runs = []
    for s in ("base", "variant"):
        r = ctx.run(s, {"args": [], "kwargs": {}}, "probe", 0, mode="probe")
        probe_runs.append(r.run_id)
        if not r.sandbox_ok: st.append(("sandbox_failure", f"{s}: probe run"))
        elif r.limit: st.append(("resource_limit", f"{s}: import hit a limit ({r.limit})"))
        elif r.phase == "import_error": st.append(("import_error", f"{s}: {r.msg}"))
        elif r.phase == "entry_missing": st.append(("unsupported_signature", f"{s}: entry_missing {r.msg}"))
        elif r.phase != "ok": st.append(("tool_error", f"{s}: probe {r.phase} {r.msg}"))
        else: sigs[s] = r.sig
    sig_ok = len(sigs) == 2 and _sig_compatible(sigs["base"], sigs["variant"])
    if len(sigs) == 2 and not sig_ok and not cfg["harness"]["api_break_probe"]:
        st.append(("unsupported_signature", "incompatible signature and api_break_probe=false"))
    units = {"base": set(), "variant": set()}
    if not st:
        try:
            la, lb = changed_lines(ctx.src["base"].decode(), ctx.src["variant"].decode())
            ex = {s: _exec_lines(ctx.src[s].decode()) for s in ctx.src}
            units = {"base": la & ex["base"], "variant": lb & ex["variant"]}
        except (SyntaxError, ValueError, UnicodeDecodeError, RecursionError) as e:
            st.append(("alignment_failed", f"{type(e).__name__}: {e}"))
    changed = frozenset((s, l) for s in units for l in units[s])
    evs, hit, brs, stop, any_lossy = [], {"base": set(), "variant": set()}, {"base": {}, "variant": {}}, None, False
    if not st:
        for inp in inputs:
            if ctx.spent >= cfg["budget"]["cpu_seconds"]:
                stop = "budget"; break
            ev, h, b, _, more = process_input(ctx, inp)
            evs.append(ev); st += more
            if ev.outcome == "SAME":  # only deterministic-confirmed SAME inputs contribute to activation
                for s in hit:
                    hit[s] |= h[s]
                    for k, v in b[s].items(): brs[s].setdefault(k, set()).update(v)
            if ev.outcome == "CONFIRMED_DIFF": stop = "witness"; break
    hit_units = frozenset((s, l) for s in hit for l in units[s] if l in hit[s])
    cov = {}
    for s in hit:
        stat = _static_branches(ctx.src[s].decode(), units[s]) if not st else set()
        got = sum(min(2, len(brs[s].get(k, ()))) for k in stat)
        cov[s] = 1.0 if not stat else got / (2 * len(stat))
    ev_all = Evidence(inputs=evs, blockers=st, changed_units=changed, hit_units=hit_units, branch_cov=cov,
                      budget_exhausted=stop == "budget", tampered=False, s2_floor=cfg["suff"]["s2_branch_floor"])
    if st and not evs:
        ev_all.inputs = None  # nothing was executed because a static blocker fired
    value, level, primary, secondary, wid, blockers, floors = decide(ev_all)
    if wid:
        refs = [wid]
    else:
        suff_body = {"level": level or "S0", "floors": floors, "branch_cov": cov, "units_total": len(changed), "units_hit": len(hit_units),
                     "unhit": sorted(map(list, changed - hit_units)), "stop_reason": stop or "inputs_exhausted",
                     "r_det": cfg["repeat"]["r_det"], "inputs_same": sum(e.outcome == "SAME" for e in evs),
                     "quarantined": sum(e.outcome == "QUARANTINED" for e in evs), "r_empty": not changed,
                     "policy_below_minimum": sys.platform == "darwin", "blockers": [list(b) for b in blockers],
                     "run_set_root": R.sha(R.canon_json(sorted(r for e in evs for r in e.run_ids)))}
        refs = [e for ev in evs for e in ev.run_ids] + probe_runs + list(ctx.vers.values())
        refs = [log.append(R.SufficiencyRecord(sorted(set(refs)), suff_body))]
    v = R.Verdict(value, level, primary, secondary, refs, ctx.pair_id)
    vid = log.append(v)
    out = {"verdict": value, "level": level, "primary": primary, "secondary": sorted(secondary), "witness_id": wid,
           "verdict_id": vid, "sufficiency_id": None if wid else refs[0], "pair_id": ctx.pair_id,
           "policy_below_minimum": sys.platform == "darwin", "cpu_seconds_spent": round(ctx.spent, 3)}
    json.dump(out, open(os.path.join(out_dir, "verdict.json"), "w"), indent=1)
    return out
