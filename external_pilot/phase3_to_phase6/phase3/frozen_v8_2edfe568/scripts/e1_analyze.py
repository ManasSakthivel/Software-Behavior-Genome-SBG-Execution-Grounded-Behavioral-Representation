"""E1 analysis (K2 determinism re-measurement). Written and fixed BEFORE the run; read-only on every input.
usage: e1_analyze.py NEW_PROC_DIR OLD_PROC_DIR OUT_JSON      (dirs hold k1_spike_per_pair.jsonl)
Pre-registered hypothesis: the QUARANTINED rate does not rise after the corrected child environment / hash seed.
Primary metric: pair-level indicator 'at least one QUARANTINED input' on run1 pairs that were driven in BOTH runs.
Decision rule (fixed before the run, alpha 0.05, one-sided exact binomial on discordant pairs, McNemar form):
  NOT SUPPORTED  if new-only discordant pairs significantly exceed old-only ones (p_increase < 0.05)
  SUPPORTED      if the new count <= old count (point estimate) and p_increase >= 0.05
  INCONCLUSIVE   otherwise (point estimate rose but not significantly)
Secondary: input-level quarantined rate (sum quarantined / sum n_inputs), verdict-distribution changes, run1-vs-run2 identity.
Pairs are NOT independent (shared projects); the p-value is descriptive, not a claim of significance. The old and new engines differ in more than
the hash seed (see report), so a difference is not attributable to the seed alone."""
import collections, json, math, os, sys

new_dir, old_dir, out = sys.argv[1:4]


def load(d):
    rows = [json.loads(l) for l in open(os.path.join(d, "k1_spike_per_pair.jsonl"))]
    return ({(r["arm"], r["pair"]): r for r in rows if r["tag"] == "run1"}, {(r["arm"], r["pair"]): r for r in rows if r["tag"] == "run2"})


(n1, n2), (o1, o2) = load(new_dir), load(old_dir)
driven = lambda r: r.get("verdict") not in ("NOT_DRIVEN", "ENGINE_NO_VERDICT")
common = sorted(k for k in n1 if k in o1 and driven(n1[k]) and driven(o1[k]))
q = lambda r: int(r.get("quarantined") or 0) > 0
b = sum(q(n1[k]) and not q(o1[k]) for k in common)  # new only
c = sum(q(o1[k]) and not q(n1[k]) for k in common)  # old only
n = b + c
p_inc = sum(math.comb(n, i) for i in range(b, n + 1)) / 2 ** n if n else 1.0
p_two = min(1.0, 2 * sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n) if n else 1.0
rate = lambda rs, f: (sum(map(f, rs)), len(rs))
new_q, old_q = rate([n1[k] for k in common], q), rate([o1[k] for k in common], q)
inp = lambda d: (sum(int(d[k].get("quarantined") or 0) for k in common), sum(int(d[k].get("n_inputs") or 0) for k in common))
rule = "NOT SUPPORTED" if p_inc < 0.05 else ("SUPPORTED" if new_q[0] <= old_q[0] else "INCONCLUSIVE")
key = lambda r: (r.get("verdict"), r.get("level"), r.get("primary"), tuple(r.get("secondary") or ()), r.get("witness_id"))
vd = lambda d: dict(collections.Counter(d[k]["verdict"] + ("/" + d[k]["level"] if d[k].get("level") else "") for k in common))
flips = [(k[1], key(o1[k])[:3], key(n1[k])[:3]) for k in common if key(o1[k])[:3] != key(n1[k])[:3]]
both = [(n1[k], n2[k]) for k in n2 if k in n1]
res = dict(n_common_driven_pairs=len(common), n_new_run1=len(n1), n_old_run1=len(o1),
           pair_level_quarantined=dict(new=new_q, old=old_q, discordant_new_only=b, discordant_old_only=c, p_increase_one_sided_exact=p_inc,
                                       p_two_sided_exact=p_two),
           input_level_quarantined=dict(new=inp(n1), old=inp(o1)), decision_rule_outcome=rule,
           verdict_distribution=dict(new=vd(n1), old=vd(o1)), verdict_flips_old_to_new=flips, n_verdict_flips=len(flips),
           new_run1_vs_run2=dict(n=len(both), identical=sum(key(x) == key(y) for x, y in both),
                                 quarantined_equal=sum(x.get("quarantined") == y.get("quarantined") for x, y in both),
                                 diffs=[(x["pair"], key(x)[:3], key(y)[:3]) for x, y in both if key(x) != key(y)]),
           old_run1_vs_run2=dict(n=len([k for k in o2 if k in o1]), identical=sum(key(o1[k]) == key(o2[k]) for k in o2 if k in o1)),
           engine_no_verdict_new=[k for k in n1 if n1[k].get("verdict") == "ENGINE_NO_VERDICT"],
           not_driven_new=sum(r.get("verdict") == "NOT_DRIVEN" for r in n1.values()), not_driven_old=sum(r.get("verdict") == "NOT_DRIVEN" for r in o1.values()),
           pairs_only_in_one_run=dict(new_only=[k for k in n1 if k not in o1], old_only=[k for k in o1 if k not in n1]))
json.dump(res, open(out, "w"), indent=1, default=list)
print(json.dumps(res, indent=1, default=list))
