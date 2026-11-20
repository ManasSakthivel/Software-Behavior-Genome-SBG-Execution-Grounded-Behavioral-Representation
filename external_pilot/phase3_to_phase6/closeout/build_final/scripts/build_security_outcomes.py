"""Build audit/security_outcomes.json from the machine-readable sources (read-only) + the report-only claims.
Each row: attack_id, suite, class, reported_outcome, outcome (audited: blocked|detected|mitigated|succeeded|unresolved|insufficient_unexplained),
evidence_status (executed-with-raw-evidence | test-code-only | report-text-only), platform, source, note."""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(PAPER))
J = lambda p: json.load(open(os.path.join(ROOT, p)))

CLS = [(r"^(A01|A02|A07_|A08|A16|A17|PY)", "in-process harness/runtime tampering"), (r"^(A03|A04|A05|A06|FD)", "result-channel / fd attack"),
       (r"^(A07c|SENSE)", "evaluation-awareness sensing"), (r"^(P06|SUBST)", "cross-pair evidence substitution"),
       (r"^(P0|EV_|CAP_|PART_|ANC_)", "post-hoc evidence tampering"), (r"^(FS|NET|PROC|ISO)", "sandbox / isolation escape"), (r"^RES", "resource exhaustion"),
       (r"^H00", "control")]
cls = lambda a: "control" if "control" in a else next(c for p, c in CLS if re.match(p, a))


def from_trust(o):
    """trust._classify outcome string -> audited category."""
    return {"DETECTED": "detected", "BLOCKED": "blocked", "NO": "mitigated", "SUCCEEDS": "succeeded"}[o.split()[0]]


rows = []
# 1. macOS original suite before/after (trust.forgery_suite, real collector, sandbox-exec)
for tag in ("before", "after"):
    src = f"results/v8_mac_security/attack_suite_{tag}.json"
    for r in J(src)["results"]:
        rows.append(dict(attack_id=r["attack"].split("_")[0], name=r["attack"], suite=f"mac_original_{tag}", **{"class": cls(r["attack"])}, reported_outcome=r["outcome"],
                         outcome=from_trust(r["outcome"]), evidence_status="executed-with-raw-evidence", platform="darwin", source=src,
                         note="effective verdict stays NDO unless trust.check(shadow=True / expected_sources) is run" if r["attack"][:3] in ("A01", "A02", "A07", "P06") and from_trust(r["outcome"]) == "detected" else ""))

# 2. this audit's re-run at HEAD 07ecd5b7 on macOS (scripts/audit_security_rerun.py)
src = "paper/IEEE_ACCESS_V8_FINAL/audit/security_rerun_darwin.json"
if os.path.exists(os.path.join(ROOT, src)):
    a = J(src)
    for r in a["forgery_suite"] + a["sensing_probes"]:
        rows.append(dict(attack_id=r["attack"].split("_")[0], name=r["attack"], suite="audit_rerun_head_darwin", **{"class": cls(r["attack"])}, reported_outcome=r["outcome"],
                         outcome=from_trust(r["outcome"]), evidence_status="executed-with-raw-evidence", platform="darwin", source=src,
                         note=f"effective_verdict={r.get('effective_verdict')}"))

# 3. Linux expanded suite (scripts/run_expanded_security_suite.py; JSON has no host/platform/timestamp metadata)
src = "results/v8/linux/expanded_security_suite_results.json"
X = J(src)
for r in X["container_74"]:
    rep = r["outcome_category"]
    if rep == "BLOCKED":
        out, note = "insufficient_unexplained", (f"verdict INSUFFICIENT in {r['duration_s']}s, shadow not_comparable, issues=[]; no cause recorded. "
                                                 "Classifier label 'BLOCKED' = verdict degraded, not OS denial")
    elif rep == "MITIGATED": out, note = "mitigated", "true DIVERGENT verdict kept (attack had no effect on the verdict); OS-level denial not recorded"
    else: out, note = "succeeded", "false NO_DIVERGENCE_OBSERVED, no check fired (pre-2edfe568 code)"
    rows.append(dict(attack_id=r["id"].split("_")[0], name=r["id"], suite="linux_container_74", **{"class": cls(r["id"])}, reported_outcome=rep, outcome=out,
                     evidence_status="executed-with-raw-evidence", platform="linux (claimed; not recorded in JSON)", source=src, note=note))
for r in X["tamper_51"]:
    rows.append(dict(attack_id=r["id"], name=r["id"] + ":" + r["description"], suite="linux_tamper_51", **{"class": cls(r["id"])}, reported_outcome=r["outcome_category"],
                     outcome="detected" if r["outcome_category"] == "DETECTED" else "succeeded", evidence_status="executed-with-raw-evidence",
                     platform="linux (claimed; not recorded in JSON)", source=src, note="validator_trusted=%s" % r["validator_trusted"]))

# 4. claims with no machine-readable evidence anywhere in the repo
R = "reports/v8/linux/"
for i, (n, c) in enumerate([("host root write", "blocked"), ("host secret access", "blocked"), ("TCP outbound", "blocked"), ("DNS", "blocked"), ("setuid/sudo", "blocked"),
                            ("parent signal/ptrace", "blocked"), ("memory flood >1GB", "mitigated"), ("CPU loop", "mitigated"), ("fork bomb", "blocked"), ("process residue", "blocked")], 1):
    rows.append(dict(attack_id=f"ISO-{i:02d}", name=n, suite="linux_podman_isolation", **{"class": "sandbox / isolation escape"}, reported_outcome=c.upper(), outcome="unresolved",
                     evidence_status="report-text-only", platform="linux (claimed)", source=R + "PODMAN_ISOLATION_REPORT.md",
                     note="no code in the repo invokes podman; no probe output file; evaluated runs use bwrap/unshare (sbgv7/isolation.py:71-78)"))
for aid, n, c, src, note in [
    ("A07c", "A07c_sense_argv_eval_environment (Linux re-test)", "DETECTED / REMEDIATED", R + "EVIDENCE_INTEGRITY_REMEDIATION.md", "no Linux result file; audit re-run on darwin at HEAD: NO EFFECT"),
    ("SENSE04", "SENSE04 post-2edfe568 re-test on Linux", "claimed fixed (commit message)", "git show 2edfe568", "commit changes code only; no Linux re-test artefact; audit re-run on darwin: NO EFFECT, but variant SENSE04b (co_filename) SUCCEEDS"),
    ("ORIG15", "original 15 + A16/A17 re-run on Linux via forgery_suite()", "COMPLETE", R + "LINUX_FINAL_EXECUTION_REPORT.md", "no Linux forgery_suite JSON in results/"),
    ("REG608", "608-case full regression on Linux", "593 passed", R + "FULL_REGRESSION_REPORT.md", "no junit/log artefact")]:
    rows.append(dict(attack_id=aid, name=n, suite="linux_report_claims", **{"class": cls(aid) if not aid.startswith(("ORIG", "REG")) else "regression claim"},
                     reported_outcome=c, outcome="unresolved", evidence_status="report-text-only", platform="linux (claimed)", source=src, note=note))

out = os.path.join(PAPER, "audit", "security_outcomes.json")
json.dump(rows, open(out, "w"), indent=1)
from collections import Counter
for s in dict.fromkeys(r["suite"] for r in rows):
    print(s, dict(Counter(r["outcome"] for r in rows if r["suite"] == s)))
assert len([r for r in rows if r["suite"] == "linux_container_74"]) == 74 and len([r for r in rows if r["suite"] == "linux_tamper_51"]) == 51
