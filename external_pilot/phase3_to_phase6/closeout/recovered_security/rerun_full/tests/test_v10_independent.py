"""Integrity tests for the v10 independent evaluation: freeze hashes, label integrity, split disjointness, headline-metric reproduction."""
import hashlib, json, pathlib, sys, subprocess
REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "experiments" / "final"))
sh = lambda p: hashlib.sha256((REPO / p).read_bytes()).hexdigest()                 # noqa: E731
jl = lambda p: [json.loads(l) for l in (REPO / p).read_text().splitlines() if l.strip()]   # noqa: E731


def test_freeze_v10_hashes_match():
    fz = json.loads((REPO / "artifacts/final/FREEZE_V10.json").read_text())
    for f, h in fz["sha256"].items():
        if f in ("experiments/final/extraction.py", "experiments/final/protocol.py", "experiments/final/entry_policy.py", "experiments/final/class_driver.py",
                 "experiments/final/static_baselines.py", "experiments/final/edit_size_analysis.py", "experiments/final/fit_weights.py", "sbg/statistics.py",
                 "sbg/extraction/dynamic/tracer.py", "sbg/v3/genome.py", "sbg/v5/state_transition_genome.py", "sbg/v5/temporal_genome_v5.py", "sbg/v6/state_transition_genome_v6.py",
                 "experiments/final/evaluate_v10.py", "experiments/final/evaluate_v4_dev.py", "experiments/final/evaluate_v9.py", "experiments/final/score_v6_experimental.py",
                 "benchmark/datasets/v10_independent/pairs_test.jsonl", "benchmark/datasets/v10_independent/manifest.json", "artifacts/final/V10_MODELS_FROZEN.json"):
            assert sh(f) == h, f
    assert json.loads((REPO / "artifacts/final/FREEZE_V10_SCORED.json").read_text())["scored_file_sha256"] == sh("artifacts/final/pairs_v10_test_v6exp.jsonl")


def test_v10_programs_disjoint_from_all_development_splits():
    v10 = {p["base_id"] for p in jl("benchmark/datasets/v10_independent/pairs_test.jsonl")}
    assert len(v10) == 19
    for d in ("benchmark/datasets/v8", "benchmark/datasets/v9_composed"):
        for s in ("train", "dev", "val", "test"):
            f = REPO / d / f"pairs_{s}.jsonl"
            if f.exists():
                assert not v10 & {p["base_id"] for p in jl(str(f.relative_to(REPO)))}


def test_v10_matched_sets_well_formed_and_variants_exist():
    ps = jl("benchmark/datasets/v10_independent/pairs_test.jsonl")
    by = {p["pair_id"]: p for p in ps}
    for p in ps:
        q = by[p["matched_pair_id"]]
        assert q["matched_pair_id"] == p["pair_id"] and {p["semantic_relation"], q["semantic_relation"]} == {"EQUIVALENT", "CHANGED"}
        assert p["base_id"] == q["base_id"] and (REPO / p["variant_path"]).exists()


def test_v10_oracle_labels_hold_for_sample():
    """Independent re-check (stdlib oracle, same protocol inputs) of 40 deterministically chosen pairs."""
    sys.path.insert(0, str(REPO / "benchmark" / "scripts"))
    from benchmark.scripts.generate_v10_independent import oracle
    ps = jl("benchmark/datasets/v10_independent/pairs_test.jsonl")
    by = {p["pair_id"]: p for p in ps}
    sample = [p for i, p in enumerate(ps) if p["semantic_relation"] == "EQUIVALENT" and i % 16 == 0][:20]
    for p in sample:
        ob, oe = oracle(REPO / p["base_path"]), oracle(REPO / p["variant_path"])
        assert ob == oe, p["pair_id"]
    for p in [x for i, x in enumerate(ps) if x["semantic_relation"] == "CHANGED" and i % 16 == 1][:20]:
        assert oracle(REPO / p["base_path"]) != oracle(REPO / p["variant_path"]), p["pair_id"]


def test_v10_evaluation_is_single_run_and_refuses_rerun():
    r = subprocess.run([sys.executable, str(REPO / "experiments/final/evaluate_v10.py"), "run"], capture_output=True, text=True, env={"PYTHONHASHSEED": "0", "PATH": ""})
    assert r.returncode != 0 and "REFUSED" in (r.stderr + r.stdout)


def test_headline_metrics_reproduce_from_scored_file():
    from sbg.statistics import auroc
    ev = json.loads((REPO / "artifacts/paper_evidence/V10_INDEPENDENT_EVALUATION.json").read_text())
    meta = {p["pair_id"]: p for p in jl("benchmark/datasets/v10_independent/pairs_test.jsonl")}
    sc = {r["pair_id"]: r for r in jl("artifacts/final/pairs_v10_test_v6exp.jsonl") if r["evaluated"]}
    groups = {}
    for pid, r in sc.items():
        m = meta[pid]
        groups.setdefault(pid if m["semantic_relation"] == "EQUIVALENT" else m["matched_pair_id"], []).append(pid)
    pop = [pid for g in groups.values() if len(g) == 2 for pid in g]
    s = [sc[p]["scores"]["sbg_v5"] for p in pop]
    y = [int(meta[p]["semantic_relation"] == "CHANGED") for p in pop]
    assert len(pop) == ev["n_pairs"] == 638
    assert round(auroc(s, y), 6) == ev["predictors"]["sbg_v5"]["auroc"]
    assert round(sum(1 for v in s if v == 0) / len(s), 4) == ev["predictors"]["sbg_v5"]["exact_zero_rate"]
    for r in jl("artifacts/final/pairs_v10_test_v6exp.jsonl"):
        assert r["evaluated"] or "scores" not in r


def test_trace_verifier_v4_passes():
    r = subprocess.run([sys.executable, str(REPO / "experiments/final/verify_trace_v4.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
