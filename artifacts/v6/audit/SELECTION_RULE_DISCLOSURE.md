# Disclosure: history of the V6 selection-rule operationalisation (written 2026-11-17T02:38:35.077969+00:00)

- The source rule (reports/v6_redesign/03_PROBLEM_LITERATURE_ARCHITECTURES.md:61) was declared before experiments but gave NO non-inferiority margin, tie criterion or simplicity order.
- Those three were operationalised by the analyst (SELECTION_RULE_OPERATIONALISATION.json, sha256 c68b2d426d05606eff9058781ed3d1d9cb0a3b6c83c9bfe5e58689c41b67c759) AFTER the single-seed ablation (ABLATION_dev.json) had been observed, and BEFORE the multi-seed, LOFO and edit-size-stratified results were computed. The 0.02 margin and the 'CI contains 0' tie criterion are therefore post-hoc relative to that earlier single-seed result.
- The architecture decision is therefore NOT fully preregistered. It is a development-set decision made under a disclosed, partly post-hoc rule.
- The comparison V6-B vs V6-B-E vs V6-B-E-A (PROTOCOL_V2) was defined after the V6-B selection results were seen, in response to the report's own finding that E is non-contributing. It is a second-stage, post-hoc development comparison.
- The original operationalisation file is preserved unmodified. Nothing in it was edited.
