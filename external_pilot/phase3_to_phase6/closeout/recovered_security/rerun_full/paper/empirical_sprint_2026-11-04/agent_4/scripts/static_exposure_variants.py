"""Static (AST-only; nothing executed, nothing scored) exposure of dataset variant files to two interpreter-dependent trace mechanisms:
 (a) constant-condition `if`/`while` (3.11+ emits line events 3.9 does not) ; (b) list/set/dict comprehensions (3.12+ inlined, no <listcomp> frame).
Reads variant .py files from the COPY only. Output outputs/static_exposure_variants.json"""
import ast, json, pathlib, collections
root = pathlib.Path(__file__).resolve().parent.parent / "copy"
def feats(path):
    try: t = ast.parse(path.read_text())
    except Exception: return None
    const_if = comp = 0
    for n in ast.walk(t):
        if isinstance(n, (ast.If, ast.While)) and isinstance(n.test, ast.Constant): const_if += 1
        if isinstance(n, (ast.ListComp, ast.SetComp, ast.DictComp)): comp += 1
    return const_if, comp
out = {}
for ds, pf in [("v8", "benchmark/datasets/v8/pairs_{}.jsonl"), ("v10_independent", "benchmark/datasets/v10_independent/pairs_{}.jsonl")]:
    for split in (["train", "val", "dev", "test"] if ds == "v8" else ["test"]):
        p = root / pf.format(split)
        if not p.exists(): continue
        byt = collections.defaultdict(lambda: [0, 0, 0, 0]); base_cache = {}
        for line in p.open():
            r = json.loads(line); vp = root / r["variant_path"]; bp = root / r["base_path"]
            if not vp.exists(): continue
            vf = feats(vp)
            if bp not in base_cache: base_cache[bp] = feats(bp)
            bf = base_cache[bp]
            if vf is None or bf is None: continue
            row = byt[r["transformation_type"]]; row[0] += 1
            row[1] += (vf[0] != bf[0])      # variant differs from base in count of constant-condition if/while
            row[2] += (vf[1] != bf[1])      # differs in comprehension count
            row[3] += (vf[1] > 0 or bf[1] > 0)  # either side contains a comprehension
        out[f"{ds}/{split}"] = {k: {"n_pairs": v[0], "const_cond_count_differs": v[1], "comprehension_count_differs": v[2], "either_side_has_comprehension": v[3]} for k, v in sorted(byt.items())}
json.dump(out, open(root.parent/"outputs"/"static_exposure_variants.json", "w"), indent=1)
for k, v in out.items():
    n = sum(x["n_pairs"] for x in v.values()); cc = sum(x["const_cond_count_differs"] for x in v.values()); cp = sum(x["either_side_has_comprehension"] for x in v.values()); cd = sum(x["comprehension_count_differs"] for x in v.values())
    print(f"{k}: {n} pairs; const-cond differs base/variant in {cc}; comprehension count differs in {cd}; either side has a comprehension in {cp}")
    print("   const-cond by type:", {t: x["const_cond_count_differs"] for t, x in v.items() if x["const_cond_count_differs"]})
