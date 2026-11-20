"""Audit re-run (read-only on repo code): trust.forgery_suite() at current HEAD plus SENSE04 and file-name-sensing variants,
through the real collector (sbgv8.collect.run_capture via trust._engine). Writes audit/security_rerun_<platform>.json."""
import json, os, platform, sys, tempfile, shutil, time, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from sbgv8 import trust
from sbgv7 import isolation

KEY = bytes(range(1, 33))
FAST = trust.FAST
SENSE = {
    "SENSE04_sense_file_name": "import os\ndef f(x):\n    return x + 1 if 'variant' in __file__ else x + 2\n",
    "SENSE04b_sense_code_filename": "def f(x):\n    return x + 1 if 'variant' in f.__code__.co_filename else x + 2\n",
    "SENSE04c_sense_spec_origin": "def f(x):\n    import sys\n    m = sys.modules.get(__name__)\n    o = getattr(getattr(m, '__spec__', None), 'origin', '') or ''\n    return x + 1 if 'variant' in o else x + 2\n",
    "SENSE04d_sense_cwd_listing": "import os\ndef f(x):\n    return x + 1 if any('variant' in n for n in os.listdir('.')) else x + 2\n",
    "SENSE01_sense_argv": "import sys\ndef f(x):\n    return x + 1 if 'harness' in sys.argv[0] else x + 2\n",
    "SENSE07_benign_control": "import time\ndef f(x):\n    time.sleep(0.01)\n    return x + 2\n",
}
t0 = time.time()
out = {"meta": {"platform": sys.platform, "host": platform.platform(), "python": sys.version.split()[0], "utc": datetime.datetime.utcnow().isoformat() + "Z",
                "caps": {k: v.get("state") for k, v in isolation.capabilities().items() if isinstance(v, dict)}}}
out["forgery_suite"] = trust.forgery_suite()["results"]
tmp = tempfile.mkdtemp(prefix="sbgv8_audit_")
try:
    rows = []
    for aid, src in SENSE.items():
        d, bp, vp, e = trust._engine(tmp, aid, trust.BASE, src, FAST, key=KEY)
        rows.append(trust._row(aid, "audit sensing probe", d, "DIVERGENT_OBSERVABLE", e, bp, vp, key=KEY))
    out["sensing_probes"] = rows
finally:
    shutil.rmtree(tmp, ignore_errors=True)
out["meta"]["duration_s"] = round(time.time() - t0, 1)
p = os.path.join(ROOT, "paper/IEEE_ACCESS_V8_FINAL/audit", f"security_rerun_{sys.platform}.json")
json.dump(out, open(p, "w"), indent=1, default=str)
for r in out["forgery_suite"] + out["sensing_probes"]:
    print(r["attack"][:46].ljust(46), str(r["verdict"])[:22].ljust(22), r.get("effective_verdict"), "|", r["outcome"][:80])
