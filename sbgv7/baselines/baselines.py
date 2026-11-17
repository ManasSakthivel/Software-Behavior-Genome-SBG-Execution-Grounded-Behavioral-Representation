"""Baselines B1..B5 for V7-B. Outcome vocabulary is deliberately NOT V7's: DIVERGE | NO_DIFF (| NOT_RUN). No baseline abstains
(B5 only inherits V6's own gate). All execution goes through sbgv7.runner.Ctx.run -> sbgv7.isolation (same sandbox, limits, comparator
as V7-B). Budget = child CPU (isolation cpu_s) + parent CPU of the calling thread (our overhead), same unit as the V7-B budget grid.
B3 is a minimal coverage-guided mutator, NOT AFL (no instrumented forkserver, no havoc/splice stages, line coverage only)."""
import csv, json, os, random, time
from sbgv6.features import changed_lines
from ..compare import compare
from ..config import load_config
from ..records import EvidenceLog
from ..runner import Ctx

DIVERGE, NO_DIFF = "DIVERGE", "NO_DIFF"


def make_ctx(base, var, entry, cfg, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "cfg.json"); json.dump(cfg, open(p, "w"))
    c = load_config(p)
    return Ctx(c, EvidenceLog(os.path.join(out_dir, "evidence.jsonl")), entry, base, var), c


def _tok(r):  # comparable form of a run
    if r.obs is not None: return r.obs
    return {"t": "limit", "k": r.limit} if r.limit else {"t": "phase", "k": r.phase}


def differs(ctx, a, b):
    """Observable difference on one input under the V7 boundary (compare()); limit/phase tokens differ iff unequal."""
    ta, tb = _tok(a), _tok(b)
    if ta["t"] in ("limit", "phase") or tb["t"] in ("limit", "phase"): return ta != tb
    return not compare(ta, tb, ctx.cfg["harness"]).equal


class Budget:
    def __init__(self, ctx, cap):
        self.ctx, self.cap, self.p0, self.s0 = ctx, cap, time.thread_time(), ctx.spent

    @property
    def used(self): return (self.ctx.spent - self.s0) + (time.thread_time() - self.p0)  # child + parent overhead

    @property
    def left(self): return self.used < self.cap


def _res(v, b, ctx, n, **kw):
    return dict(verdict=v, cpu_s=round(b.used, 3), child_cpu_s=round(ctx.spent - b.s0, 3), n_runs=n, **kw)


def _ok(runs): return all(r.sandbox_ok for r in runs)


def b1(ctx, inputs, cap):
    """Same inputs, single run per side, report diverge/no-diff. No replay, no repeats, no sufficiency."""
    b, n = Budget(ctx, cap), 0
    for i in inputs:
        if not b.left: break
        x, y = ctx.run("base", i, "primary", 0), ctx.run("variant", i, "primary", 0); n += 2
        if not _ok([x, y]): return _res("ERROR", b, ctx, n, detail="sandbox")
        if differs(ctx, x, y): return _res(DIVERGE, b, ctx, n, input=i["id"])
    return _res(NO_DIFF, b, ctx, n)


def b1_rep(ctx, inputs, cap):
    """B1 plus V7-B's repeat counts (r_det per side per input; r_replay fresh replays on a candidate), no sufficiency/activation gate,
    no alternate-control runs. DIVERGE iff differing AND both sides self-consistent AND replays reproduce; irreproducible = not counted."""
    rep, b, n = ctx.cfg["repeat"], Budget(ctx, cap), 0
    for i in inputs:
        if not b.left: break
        runs = {s: [ctx.run(s, i, "primary", 0)] for s in ("base", "variant")}
        for s in runs:
            for k in range(1, rep["r_det"]):
                runs[s].append(ctx.run(s, i, "repeat", k))
        n += 2 * rep["r_det"]
        if not _ok(runs["base"] + runs["variant"]): return _res("ERROR", b, ctx, n, detail="sandbox")
        if not all(not differs(ctx, runs[s][0], r) for s in runs for r in runs[s]): continue  # not self-consistent
        if differs(ctx, runs["base"][0], runs["variant"][0]):
            rp = {s: [ctx.run(s, i, "replay", k) for k in range(rep["r_replay"])] for s in runs}; n += 2 * rep["r_replay"]
            if all(not differs(ctx, runs[s][0], r) for s in rp for r in rp[s]): return _res(DIVERGE, b, ctx, n, input=i["id"])
    return _res(NO_DIFF, b, ctx, n)


def plain(n):
    """harness canonical node -> plain JSON-ish value (tuple/set -> list) for B2 expected-output comparison."""
    t = n[0]
    if t == "none": return None
    if t in ("bool", "str"): return n[1]
    if t == "int": return int(n[1])
    if t == "float": return float(n[1])
    if t in ("list", "tuple", "set", "frozenset"): return [plain(x) for x in n[1]]
    if t == "dict": return {json.dumps(plain(k)): plain(v) for k, v in n[1]}
    return ("opaque", t)


def b2(ctx, inputs, expected, cap):
    """Test replay: each declared (input, expected) is a test; pass = returned value equals expected (tuples == lists).
    DIVERGE iff any test's pass/fail differs between versions (fix or regression). Needs declared expected outputs."""
    b, n, diff = Budget(ctx, cap), 0, []
    for i, exp in zip(inputs, expected):
        if not b.left: break
        r = {s: ctx.run(s, i, "primary", 0) for s in ("base", "variant")}; n += 2
        if not _ok(r.values()): return _res("ERROR", b, ctx, n, detail="sandbox")
        ps = {s: r[s].obs is not None and r[s].obs["t"] == "returned" and plain(r[s].obs["ret"]) == exp for s in r}
        if ps["base"] != ps["variant"]: diff.append((i["id"], ps["base"], ps["variant"]))
    return _res(DIVERGE if diff else NO_DIFF, b, ctx, n, tests_changed=diff, n_tests=len(expected))


def _mut(v, rng, depth=0):
    """Mutate a JSON value (type-preserving mostly)."""
    if isinstance(v, bool): return (not v) if rng.random() < .8 else rng.choice([0, 1, None])
    if isinstance(v, int):
        return rng.choice([v + 1, v - 1, -v, 0, 1, v * 2, v // 2, rng.randint(-10, 10), rng.randint(-2**31, 2**31), v ^ (1 << rng.randint(0, 8))])
    if isinstance(v, float): return rng.choice([v + 1.0, -v, 0.0, v * 2, v / 2, rng.uniform(-10, 10), float(int(v))])
    if isinstance(v, str):
        if not v or rng.random() < .2: return v + rng.choice("abz 09_\n")
        k = rng.randrange(len(v)); m = rng.random()
        return v[:k] + v[k + 1:] if m < .35 else v[:k] + rng.choice("abz 09_") + v[k:] if m < .7 else v[:k] + v[k:].upper()
    if isinstance(v, list):
        if not v or rng.random() < .25: return v + [rng.choice([0, 1, -1, "a", None, 2])] if not v or not isinstance(v[0], list) else v + [list(v[0])]
        k = rng.randrange(len(v)); m = rng.random()
        if m < .2: return v[:k] + v[k + 1:]
        if m < .35: return v[:k] + [v[k]] + v[k:]
        if m < .45: return list(reversed(v))
        w = list(v); w[k] = _mut(v[k], rng, depth + 1); return w
    if isinstance(v, dict):
        if not v: return {"a": 0}
        k = rng.choice(sorted(v)); w = dict(v)
        if rng.random() < .15: del w[k]
        else: w[k] = _mut(v[k], rng, depth + 1)
        return w
    return rng.choice([None, 0, 1])


def b3(ctx, inputs, cap, seed, max_execs=60):
    """Coverage-guided random differential: seed corpus = the shared inputs (run first, same as B1); then mutate a corpus entry's args,
    run both versions once, keep the mutant iff it hits a (side,line) not seen before. Decision rule = B1's (single run). Seeded.
    max_execs caps mutants for wall-clock tractability (documented deviation: the CPU cap alone permits ~1000+)."""
    rng, b, n = random.Random(seed), Budget(ctx, cap), 0
    corpus, seen, k = [], set(), 0
    queue = list(inputs)
    while b.left:
        if queue: i = queue.pop(0)
        elif k >= max_execs or not corpus: break
        else:
            par = rng.choice(corpus); a = json.loads(json.dumps(par["args"])); j = rng.randrange(len(a)) if a else None
            if j is not None:
                for _ in range(rng.choice([1, 1, 2, 3])): a[j] = _mut(a[j], rng)
            i = {"id": f"m{k}", "args": a, "kwargs": par.get("kwargs", {})}; k += 1
        x, y = ctx.run("base", i, "primary", 0), ctx.run("variant", i, "primary", 0); n += 2
        if not _ok([x, y]): return _res("ERROR", b, ctx, n, detail="sandbox")
        if differs(ctx, x, y): return _res(DIVERGE, b, ctx, n, input=i["id"], mutants=k, corpus=len(corpus), seed=seed, witness_args=i["args"])
        cov = {("b", l) for l in x.hits} | {("v", l) for l in y.hits}
        if cov - seen or not corpus: corpus.append(i)  # first input always kept
        seen |= cov
    return _res(NO_DIFF, b, ctx, n, mutants=k, corpus=len(corpus), lines_seen=len(seen), seed=seed)


def edit_size(base_path, var_path):
    la, lb = changed_lines(open(base_path).read(), open(var_path).read())
    return len(la) + len(lb)


def tune_threshold(sizes, pos):
    """Largest-balanced-accuracy t for 'DIVERGE iff edit_size >= t'; ties -> smallest t. DEVELOPMENT rows only."""
    best = None
    for t in sorted(set(sizes)) + [max(sizes) + 1]:
        tp = sum(s >= t and p for s, p in zip(sizes, pos)); tn = sum(s < t and not p for s, p in zip(sizes, pos))
        P, N = sum(pos), len(pos) - sum(pos)
        ba = (tp / max(1, P) + tn / max(1, N)) / 2
        if best is None or ba > best[0] + 1e-12: best = (ba, t)
    return best[1], best[0]


def b4(size, t): return DIVERGE if size >= t else NO_DIFF


def load_c0g(root):
    """B5 ARTIFACT LOOKUP (no retraining, no re-scoring): V6 C0g_V6B_gated LR scores from frozen V6 artifacts.
    Returns {pair_id: (score, status, label, src)}. Holdout CSVs were scored once by V6; train OOF scores are cross-validated."""
    out = {}
    for r in csv.DictReader(open(os.path.join(root, "artifacts/v6/final/predictions_final.csv"))):
        if r["model"] == "C0g_V6B_gated" and r["clf"] == "LR":
            out[r["pair_id"]] = (float(r["oof_score_mean3seeds"]), r["status"], int(r["label"]), "train_oof")
    for name in ("v10", "v8test", "quixbugs_declared"):
        for r in csv.DictReader(open(os.path.join(root, f"artifacts/v6/holdout/results/predictions_{name}.csv"))):
            out[r["pair_id"]] = (float(r["C0g_V6B_gated|LR"]), r["status"], int(r["label"]), name)
    return out
