#!/usr/bin/env python3
"""P01: public-metadata fetch (GitHub API / HF API / PyPI JSON). Read-only metadata; no dataset payload downloaded.
Output: P01_metadata.json  (UTC timestamp recorded)."""
import json, urllib.request, datetime, sys
def get(u):
    try:
        r = urllib.request.Request(u, headers={"User-Agent": "wpd-d3-feasibility"})
        return json.load(urllib.request.urlopen(r, timeout=15))
    except Exception as e:
        return {"_error": repr(e)}
out = {"fetched_utc": datetime.datetime.utcnow().isoformat() + "Z", "github": {}, "hf": {}, "pypi": {}}
for repo in ["rjust/defects4j","soarsmu/BugsInPy","jkoppel/QuixBugs","ManySStuBs4J/ManySStuBs4J","microsoft/neurips21-self-supervised-bug-detection-and-repair",
             "BugSwarm/bugswarm","codeflaws/codeflaws","gitbugactions/gitbug-java","gitbugactions/gitbug-java","IBM/Project_CodeNet","google-deepmind/code_contests",
             "microsoft/CodeXGLUE","tdurieux/RefactoringMiner" ,"tsantalis/RefactoringMiner","githubhuyang/refactory","bigcode-project/octopack",
             "mutpy/mutpy","boxed/mutmut","sixty-north/cosmic-ray","evalplus/evalplus","openai/human-eval","python/cpython","TypeBugs/TypeBugs","ExpertiseModel/Defects4Py",
             "Jungfrau-ai/debugbench","FSoft-AI4Code/CodeCapybara","rjust/defects4j","Spirals-Team/defects4j-dissection","cqse/refactoring-oracle","nlp-uoregon/trankit"]:
    if repo in out["github"]: continue
    d = get(f"https://api.github.com/repos/{repo}")
    out["github"][repo] = {k: (d.get(k) if not isinstance(d.get(k), dict) else d[k].get("spdx_id")) for k in ("full_name","description","license","language","size","stargazers_count","pushed_at","archived","_error","message")}
for ds in ["bigcode/humanevalpack","google-research-datasets/mbpp","deepmind/code_contests","codeparrot/apps","google/code_x_glue_cc_defect_detection","google/code_x_glue_cc_clone_detection_big_clone_bench",
           "google/code_x_glue_cc_clone_detection_poj104","openai/openai_humaneval","evalplus/humanevalplus","evalplus/mbppplus","Rtian/DebugBench","bigcode/humanevalpack","iNeil77/pyrefactor",
           "mhhmm/leetcode-solutions-python","nuprl/CanItEdit","Muennighoff/humanevalfix"]:
    d = get(f"https://huggingface.co/api/datasets/{ds}")
    cd = d.get("cardData") or {}
    out["hf"][ds] = {"license": cd.get("license"), "gated": d.get("gated"), "downloads": d.get("downloads"), "_error": d.get("_error"), "siblings": [s["rfilename"] for s in d.get("siblings", [])][:12]}
for pkg in ["mutmut","cosmic-ray","MutPy","mutatest","python-minifier","rope","libcst","bugsinpy","datasets","pyminifier","pyupgrade","astor","refactor","autoflake","yapf","black"]:
    d = get(f"https://pypi.org/pypi/{pkg}/json")
    i = d.get("info", {})
    out["pypi"][pkg] = {"version": i.get("version"), "license": i.get("license") or i.get("license_expression"), "requires_python": i.get("requires_python"),
                        "requires_dist": i.get("requires_dist"), "summary": i.get("summary"), "_error": d.get("_error"),
                        "upload_time": ((d.get("urls") or [{}])[0].get("upload_time"))}
json.dump(out, open("P01_metadata.json", "w"), indent=1)
print("ok", sum(1 for v in out["github"].values() if "_error" in v and v["_error"]), "github errors")
