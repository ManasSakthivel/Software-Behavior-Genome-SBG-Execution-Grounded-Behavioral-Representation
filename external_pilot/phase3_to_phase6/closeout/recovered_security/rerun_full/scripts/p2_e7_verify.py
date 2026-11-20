#!/usr/bin/env python
"""Phase 2 E7 evidence replay + corruption suite (pre-registered in reports/phase2/E3_E7_PROTOCOLS.md).
  p2_e7_verify.py run --out DIR --src LABEL=DIR [LABEL=DIR ...] [--workers 2] [--no-corruption]
Part A: `python -m sbgv7 verify` on every evidence dir under each src (dirs holding evidence.jsonl AND verdict.json, excluding */baselines/*),
        tabulated as exit code x verdict class (DIVERGENT_OBSERVABLE | NO_DIVERGENCE_OBSERVED/S1 | /S2 | INSUFFICIENT:<primary>).
Part B: corruption suite on COPIES inside DIR/corruption (originals are never touched) against one DIV, one NDO and one INSUFFICIENT dir
        (first in sorted order). Expected exit codes are fixed in EXPECT below BEFORE any run; deviations are reported, not adjusted.
Exit codes of verify (sbgv7/__main__.py): 0 verified, 1 mismatch/tamper, 2 unreadable/missing, 4 evidence omitted by size cap.
Refuses an existing DIR. -h exits 0 before any work; bad usage exits 2."""
import argparse, collections, glob, json, os, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = os.path.join(ROOT, ".venv/bin/python")
# case -> (expected exit, note). "KNOWN_LIMITATION" cases are expected to pass verify (exit 0) = not detected.
EXPECT = {
    "flip_byte_in_record": (1, "one byte of the middle of a Run line flipped (JSON error or chain break)"),
    "truncate_drop_last_record": (1, "Verdict line removed, chain intact up to there"),
    "truncate_mid_line": (1, "file cut at half its size"),
    "delete_middle_record": (1, "a middle line removed, chain not repaired"),
    "remove_package_rechained": (1, "EvidencePackage line removed, chain recomputed, verdict.json log_head updated"),
    "break_chain_prev": (1, "a prev field altered"),
    "verdict_json_changed": (1, "verdict.json verdict value altered"),
    "verdict_json_log_head_changed": (1, "verdict.json log_head altered"),
    "evidence_missing": (2, "evidence.jsonl deleted"),
    "source_omitted_rechained": (4, "ProgramVersion src replaced by src_omitted (size-cap simulation), chain repaired"),
    "forge_meta_timing_rechained": (0, "KNOWN_LIMITATION: Run meta cpu_s/wall_s edited, chain + log_head repaired: not verified, not detected"),
    "forge_run_status_rechained": (0, "KNOWN_LIMITATION: Run summary status/detail edited (facts taken as recorded), chain + log_head repaired"),
    "forge_without_rechain": (1, "negative control: the same timing edit WITHOUT repairing the chain"),
    "delete_verdict_json": (0, "KNOWN_LIMITATION: verdict.json is optional for verify; its removal is not detected"),
}


def verify(d):
    r = subprocess.run([PY, "-m", "sbgv7", "verify", d], cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout.strip() or r.stderr.strip())[-300:]


def klass(v):
    if v["verdict"] == "NO_DIVERGENCE_OBSERVED": return f"NO_DIVERGENCE_OBSERVED/{v['level']}"
    return f"INSUFFICIENT:{v['primary']}" if v["verdict"] == "INSUFFICIENT" else v["verdict"]


def discover(d):
    return sorted(os.path.dirname(p) for p in glob.glob(os.path.join(d, "**", "evidence.jsonl"), recursive=True)
                  if "/baselines/" not in p and os.path.exists(os.path.join(os.path.dirname(p), "verdict.json")))


def part_a(out, srcs, workers):
    items = [(label, dd) for label, d in srcs for dd in discover(d)]
    def job(it):
        label, dd = it; v = json.load(open(os.path.join(dd, "verdict.json"))); rc, msg = verify(dd)
        return dict(src=label, dir=dd, klass=klass(v), recorded_verdict=v["verdict"], exit=rc, msg=msg)
    with ThreadPoolExecutor(workers) as ex: rows = list(ex.map(job, items))
    with open(os.path.join(out, "verify_results.jsonl"), "w") as f:
        for r in rows: f.write(json.dumps(r) + "\n")
    tab = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for r in rows: tab[r["src"]][r["klass"]][r["exit"]] += 1
    summ = {s: {k: dict(sorted(c.items())) for k, c in sorted(t.items())} for s, t in tab.items()}
    summ["_totals"] = dict(sorted(collections.Counter(r["exit"] for r in rows).items()))
    summ["_n_dirs"] = len(rows); summ["_failures"] = [r["dir"] for r in rows if r["exit"] != 0]
    json.dump(summ, open(os.path.join(out, "verify_table.json"), "w"), indent=1)
    return rows, summ


def rewrite(path, mutate, rechain=True):
    """Parse the log, apply mutate(list of entries) and optionally recompute seq/prev/hash; returns the new head hash."""
    sys.path.insert(0, ROOT)
    from sbgv7.records import canon_json, sha
    es = [json.loads(l) for l in open(path)]; es = mutate(es) or es
    prev = "0" * 64
    with open(path, "w") as f:
        for i, e in enumerate(es):
            if rechain: e["seq"], e["prev"], e["hash"] = i, prev, sha(prev + canon_json(e["rec"]))
            prev = e["hash"]; f.write(canon_json(e) + "\n")
    return prev


def set_head(d, head):
    p = os.path.join(d, "verdict.json"); v = json.load(open(p)); v["log_head"] = head; json.dump(v, open(p, "w"), indent=1)


def first_kind(es, kind): return next(i for i, e in enumerate(es) if e["rec"]["kind"] == kind)


def make_cases(src, dst):
    """Returns {case: (dir, ...)} after building each corrupted copy."""
    out = {}
    def cp(name):
        d = os.path.join(dst, name); shutil.copytree(src, d); out[name] = d; return d, os.path.join(d, "evidence.jsonl")
    d, p = cp("flip_byte_in_record"); b = bytearray(open(p, "rb").read()); lines = b.split(b"\n")
    i = next(k for k, l in enumerate(lines) if b'"kind":"Run"' in l); lines[i][len(lines[i]) // 2] ^= 0x01; open(p, "wb").write(b"\n".join(lines))
    d, p = cp("truncate_drop_last_record"); ls = open(p).read().splitlines(True); open(p, "w").writelines(ls[:-1])
    d, p = cp("truncate_mid_line"); b = open(p, "rb").read(); open(p, "wb").write(b[: len(b) // 2])
    d, p = cp("delete_middle_record"); ls = open(p).read().splitlines(True); del ls[len(ls) // 2]; open(p, "w").writelines(ls)
    d, p = cp("remove_package_rechained"); set_head(d, rewrite(p, lambda es: [e for e in es if e["rec"]["kind"] != "EvidencePackage"]))
    d, p = cp("break_chain_prev"); es = [json.loads(l) for l in open(p)]; es[1]["prev"] = "f" * 64
    open(p, "w").write("".join(json.dumps(e) + "\n" for e in es))
    d, p = cp("verdict_json_changed"); v = json.load(open(d + "/verdict.json")); v["verdict"] = "NO_DIVERGENCE_OBSERVED" if v["verdict"] != "NO_DIVERGENCE_OBSERVED" else "DIVERGENT_OBSERVABLE"; json.dump(v, open(d + "/verdict.json", "w"))
    d, p = cp("verdict_json_log_head_changed"); set_head(d, "0" * 64)
    d, p = cp("evidence_missing"); os.remove(p)
    def omit(es):
        for e in es:
            if e["rec"]["kind"] == "ProgramVersion": m = e["rec"]["meta"]; m["src_omitted"] = len(m.pop("src"))
    d, p = cp("source_omitted_rechained"); set_head(d, rewrite(p, omit))
    def timing(es):
        e = es[first_kind(es, "Run")]; e["rec"]["meta"]["cpu_s"] = 123.456; e["rec"]["meta"]["wall_s"] = 123.456
    d, p = cp("forge_meta_timing_rechained"); set_head(d, rewrite(p, timing))
    def status(es):
        e = es[first_kind(es, "Run")]; e["rec"]["body"]["summary"]["status"] = "FORGED"; e["rec"]["body"]["summary"]["detail"] = "forged"
    d, p = cp("forge_run_status_rechained"); set_head(d, rewrite(p, status))
    d, p = cp("forge_without_rechain"); rewrite(p, timing, rechain=False)
    d, p = cp("delete_verdict_json"); os.remove(d + "/verdict.json")
    return out


def part_b(out, rows):
    pick = {}
    for r in sorted(rows, key=lambda r: r["dir"]):
        if r["exit"] == 0: pick.setdefault(r["klass"].split(":")[0].split("/")[0], r)
    res = []
    for cls, r in sorted(pick.items()):
        dst = os.path.join(out, "corruption", cls); os.makedirs(dst)
        for case, d in make_cases(r["dir"], dst).items():
            rc, msg = verify(d); exp = EXPECT[case][0]
            res.append(dict(source_class=cls, source_dir=r["dir"], case=case, expected=exp, observed=rc, as_expected=rc == exp, note=EXPECT[case][1], msg=msg))
    json.dump(res, open(os.path.join(out, "corruption_results.json"), "w"), indent=1)
    return res


def cmd_run(a):
    out = os.path.abspath(a.out)
    if os.path.exists(out): sys.exit(f"error: {out} exists; refusing to reuse")
    srcs = [s.split("=", 1) for s in a.src]
    for _, d in srcs:
        if not os.path.isdir(d): sys.exit(f"error: no such dir {d}")
    os.makedirs(out)
    rows, summ = part_a(out, srcs, a.workers); print(json.dumps(summ, indent=1))
    if not a.no_corruption:
        res = part_b(out, rows)
        print(f"corruption suite: {sum(r['as_expected'] for r in res)}/{len(res)} as expected; deviations:", [(r['source_class'], r['case'], r['expected'], r['observed']) for r in res if not r["as_expected"]])


def parser():
    ap = argparse.ArgumentParser(prog="p2_e7_verify.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run"); r.add_argument("--out", required=True); r.add_argument("--src", nargs="+", required=True)
    r.add_argument("--workers", type=int, default=2); r.add_argument("--no-corruption", action="store_true")
    return ap


if __name__ == "__main__":
    cmd_run(parser().parse_args())
