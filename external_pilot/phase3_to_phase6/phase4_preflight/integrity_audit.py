"""Corrected Phase 4 preflight matrix (v2) and blocker recount. Non-executing.

Signature facts are read from the PARENT commit with ast (see ENTRY table). Test-evidence flags
(CONTAINER, CALLABLE, NONSCALAR, TIME, CLASS-by-construction) are judgments tied to the cited test
lines in EVIDENCE. Adapter v1 blockers: CLASS, CONTAINER, CALLABLE, DEFAULT, NONSCALAR, VARKW, KWONLY.
TIME is a validity risk, not an adapter refusal, so it is reported separately and not counted as a blocker.
"""
import ast, csv, json, subprocess, sys
from collections import Counter
ROOT = "/Users/manassakthivel/SBG_EXTERNAL_PILOT"
D = f"{ROOT}/phase3_to_phase6/phase4_preflight"
S = json.load(open(f"{ROOT}/audit/phase2/PILOT_CASE_SHORTLIST_DATA.json"))

# id -> (repo, file, owner, function) for the entry the regression test calls, at parent
ENTRY = {
 "schedule:90bfdf355": ("schedule","schedule/__init__.py","Job","__str__"),
 "schedule:f19998bcf": ("schedule","schedule/__init__.py","Job","_schedule_next_run"),
 "schedule:bcfa35789": ("schedule","schedule/__init__.py","Scheduler","run_all"),
 "funcy:6cfcd4eec": ("funcy","funcy/flow.py",None,"once_per_args"),
 "funcy:2da8b5e04": ("funcy","funcy/objects.py",None,"wrap_prop"),
 "funcy:980f0279a": ("funcy","funcy/flow.py",None,"limit_error_rate"),
 "funcy:848dd6dd2": ("funcy","funcy/seqs.py",None,"lpartition"),
 "funcy:e148cc9ab": ("funcy","funcy/calc.py",None,"memoize"),
 "funcy:6c111987f": ("funcy","funcy/flow.py",None,"throttle"),
 "funcy:e068b6400": ("funcy","funcy/colls.py",None,"where"),
 "funcy:54ed07a6a": ("funcy","funcy/seqs.py",None,"flatten"),
 "more-itertools:2b8d5cddc": ("more-itertools","more_itertools/more.py","bucket","__init__"),
 "more-itertools:71e070b35": ("more-itertools","more_itertools/more.py",None,"all_unique"),
 "more-itertools:6b1907de2": ("more-itertools","more_itertools/more.py","seekable","__init__"),
 "boltons:d0a284fc7": ("boltons","boltons/setutils.py","IndexedSet","__getitem__"),
}
# judgments from the regression test (added lines, see CORRECTIONS/EVIDENCE in the report)
TEST = {
 "schedule:90bfdf355": dict(CLASS="Job built via every().minute.do(...)", CALLABLE="job_fun partial (test line: functools.partial)", HARNESS_DEFAULT="every(interval=1)", HARNESS_VARKW="do(job_func, *args, **kwargs)"),
 "schedule:f19998bcf": dict(CLASS="Job built via every().wednesday.at().do(...)", CALLABLE="mock_job", TIME="mock_datetime(2020,11,25,...)", HARNESS_DEFAULT="every(interval=1)", HARNESS_VARKW="do(job_func, *args, **kwargs)"),
 "schedule:bcfa35789": dict(CLASS="module-level default Scheduler and schedule.jobs", CALLABLE="stop_job closure", HARNESS_DEFAULT="every(interval=1)", HARNESS_VARKW="do(job_func, *args, **kwargs)"),
 "funcy:6cfcd4eec": dict(CALLABLE="initialize (decorated function)", KWONLY_IN_INPUT="initialize(*, language='en') keyword-only with default"),
 "funcy:2da8b5e04": dict(CLASS="test defines classes A and Manager; property wrapped in class body"),
 "funcy:980f0279a": dict(NONSCALAR="timeout parametrised with timedelta(seconds=0.5)", CALLABLE="fail decorated function", TIME="fail.blocked -= timedelta(seconds=1)"),
 "funcy:848dd6dd2": dict(CONTAINER="iter(range(10)) and list(range(10)) as seq"),
 "funcy:e148cc9ab": dict(CALLABLE="total and key_func=tuple", CONTAINER="argument [1, 2] passed to cached function"),
 "funcy:6c111987f": dict(NONSCALAR="timedelta(seconds=s) (defect region); int is the scalar control", CALLABLE="typ lambda builds the input", TIME="monkeypatch clock"),
 "funcy:e068b6400": dict(CONTAINER="data = [{'a': 1}, {'b': 2}]"),
 "funcy:54ed07a6a": dict(CONTAINER="nested lists and tuples", CALLABLE="follow=is_list"),
 "more-itertools:2b8d5cddc": dict(CLASS="bucket(iterable, key=lambda)", CONTAINER="iterable=[10, 20, 11, 21]", CALLABLE="key lambda"),
 "more-itertools:71e070b35": dict(CONTAINER="['A','B','C','b']", CALLABLE="CaseFold instance (user class with __call__)"),
 "more-itertools:6b1907de2": dict(CLASS="seekable([...], maxlen=0)", CONTAINER="[10, 20, 30]", KWARGS_IN_HARNESS="maxlen keyword"),
 "boltons:d0a284fc7": dict(CLASS="IndexedSet(range(10))", CONTAINER="range(10)", HARNESS_DEFAULT="IndexedSet.__init__(other=None) constructor", KWARGS_IN_HARNESS="pop(2) mutates state before getitem"),
}

def sig(repo, commit, path, owner, name):
    src = subprocess.run(["git","-C",f"{ROOT}/{repo}","show",f"{commit}:{path}"],capture_output=True,text=True).stdout
    t = ast.parse(src); fn = None
    for n in t.body:
        if owner is None and isinstance(n, ast.FunctionDef) and n.name == name: fn = n
        if owner and isinstance(n, ast.ClassDef) and n.name == owner:
            for b in n.body:
                if isinstance(b, ast.FunctionDef) and b.name == name: fn = b
    a = fn.args; pos = [x.arg for x in a.args]; nd = len(a.defaults)
    defaulted = pos[len(pos)-nd:] if nd else []
    kwo = [x.arg for x in a.kwonlyargs]
    kwd = [x.arg for x, d in zip(a.kwonlyargs, a.kw_defaults) if d is not None]
    return dict(params=pos, defaulted=defaulted, kwonly=kwo, kwonly_defaulted=kwd,
                varkw=a.kwarg.arg if a.kwarg else None, varargs=a.vararg.arg if a.vararg else None)

rows = []
for i, s in enumerate(S, 1):
    key = f"{s['repo']}:{s['commit'][:9]}"
    repo, path, owner, name = ENTRY[key]
    sg = sig(repo, s["parent"], path, owner, name)
    tj = TEST[key]
    b = {}
    b["CLASS"] = tj.get("CLASS") or ("owner class" if owner else "")
    b["CONTAINER"] = tj.get("CONTAINER", "")
    b["CALLABLE"] = tj.get("CALLABLE", "") or tj.get("KWONLY_IN_INPUT", "") and "" or ""
    b["DEFAULT"] = "; ".join(x for x in [("entry defaulted: " + ",".join(sg["defaulted"])) if sg["defaulted"] else "", tj.get("HARNESS_DEFAULT","")] if x)
    if key == "funcy:6cfcd4eec":
        b["DEFAULT"] = "input function kw-only default: language='en'"
    if key == "bcfa35789" : pass
    b["NONSCALAR"] = tj.get("NONSCALAR", "")
    b["VARKW"] = "; ".join(x for x in [("entry **" + sg["varkw"]) if sg["varkw"] else "", tj.get("HARNESS_VARKW","")] if x)
    if key == "funcy:e068b6400": b["VARKW"] = "entry **cond"
    b["KWONLY"] = ("entry kw-only: " + ",".join(sg["kwonly"])) if sg["kwonly"] else tj.get("KWONLY_IN_INPUT", "")
    b["TIME"] = tj.get("TIME", "")
    # Adapter v1 blocking categories (TIME excluded: validity risk, not refusal)
    blockers = [k for k in ["CLASS","CONTAINER","CALLABLE","DEFAULT","NONSCALAR","VARKW","KWONLY"] if b[k]]
    rows.append(dict(case_id=f"C{i:02d}", case=key, repository=s["repo"], buggy_commit=s["parent"], fixed_commit=s["commit"],
        entry=(f"{owner}.{name}" if owner else name), entry_file=path, entry_params=";".join(sg["params"]),
        **{f"blk_{k}": b[k] for k in ["CLASS","CONTAINER","CALLABLE","DEFAULT","NONSCALAR","VARKW","KWONLY","TIME"]},
        blocker_categories=";".join(blockers), n_blocker_categories=len(blockers),
        adapter_v1_compatible="NO" if blockers else "YES"))

json.dump(rows, open(f"{D}/matrix_v2.json","w"), indent=1)
with open(f"{D}/EXTERNAL_CASE_COMPATIBILITY_MATRIX_v2.csv","w",newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

cats = ["CLASS","CONTAINER","CALLABLE","DEFAULT","NONSCALAR","VARKW","KWONLY","TIME"]
print("cases", len(rows))
print("per-category case counts (overlapping):")
for c in cats:
    print(f"  {c}: {sum(1 for r in rows if r[f'blk_{c}'])}")
unique_blocked = [r for r in rows if r["n_blocker_categories"] > 0]
print("unique cases with >=1 adapter blocker:", len(unique_blocked))
print("compatible with v1:", sum(1 for r in rows if r["adapter_v1_compatible"]=="YES"))
print("cases with >=2 blocker categories:", sum(1 for r in rows if r["n_blocker_categories"]>=2))
print("blocker-count distribution:", dict(sorted(Counter(r["n_blocker_categories"] for r in rows).items())))
