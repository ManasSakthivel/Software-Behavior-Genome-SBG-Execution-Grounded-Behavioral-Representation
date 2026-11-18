"""Synthetic EvidenceRecords with KNOWN generative truth (test helper; also the pre-data fallback for experiments/v8).
modes: 'mult'     risk depends on multiplicity m only (ERS feature = pure noise)
       'ers'      risk depends on a hidden latent h that profile features cannot see; ERS stand-in feature = h + small noise
       'ers_null' same as 'mult' (ERS feature pure noise)  [kept separate for readability]
Projects share a random effect (cluster correlation). ~15% of pairs carry a witness (CONFIRMED_DIFF, y=1, not eligible)."""
import numpy as np
from sbgv8.schema import EvidenceRecord, InputEvidence

CH = ["outcome", "exception", "side_effect", "api"]


def make_records(n_proj=60, per_proj=6, mode="mult", seed=0, proj_sd=0.6, split="development", p_witness=0.15):
    rng = np.random.default_rng(seed); recs = []
    for p in range(n_proj):
        u = rng.normal(0, proj_sd)
        for j in range(per_proj):
            m = int(rng.integers(1, 7)); act = float(rng.choice([0.5, 1.0])); h = float(rng.normal())
            wit = rng.random() < p_witness
            if wit: logit = 5.0
            elif mode == "ers": logit = -1.0 + 1.4 * h + u
            else: logit = -1.0 - 0.9 * (m - 3.5) + u
            y = 1 if wit else int(rng.random() < 1 / (1 + np.exp(-logit)))
            units = [10, 11]; hit = units if act == 1.0 else [10]
            ins = [InputEvidence(f"i{k}", "SAME", obs_fingerprint=f"fp{k}", n_repeat_runs=1, channels_present=list(CH),
                                 hits={"base": list(hit), "variant": list(hit)}) for k in range(m)]
            if wit: ins.append(InputEvidence("w", "CONFIRMED_DIFF", obs_fingerprint="wfp", channels_present=list(CH)))
            hobs = h + rng.normal(0, 0.3) if mode == "ers" else float(rng.normal())
            recs.append(EvidenceRecord(pair_id=f"p{p}_{j}", project=f"proj{p}", split=split, y=y, inputs=ins,
                                       v7b_verdict="DIVERGENT_OBSERVABLE" if wit else ("NO_DIVERGENCE_OBSERVED" if act == 1.0 else "INSUFFICIENT"),
                                       changed_units={"base": list(units), "variant": list(units)}, meta={"h_obs": float(hobs)}))
    return recs


def ers_factory(model, seed=0):
    """Stand-in for ERS response features: reads the synthetic meta value (test-only; real ERS reads evidence perturbations)."""
    return (lambda rec: {"ers_hid": rec.meta["h_obs"]}), ["ers_hid"]
