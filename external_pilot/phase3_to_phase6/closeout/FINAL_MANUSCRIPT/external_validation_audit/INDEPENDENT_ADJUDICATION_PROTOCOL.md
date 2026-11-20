# Independent blind adjudication protocol
New file; linked from `../README.md`. **No adjudication has been performed, no reviewers exist or are named, and no result is invented.** Companion files: `adjudication_form_template.csv`, `ADJUDICATION_REGISTRY.json` (both empty).

## Existing export is not blind
`results/v8/independent-validation/blinded_adjudication_cases.json`: `case_id` equals `pair_id`, and 130 of 250 ids contain `bug_` or `non_behav`; descriptions contain "fix" for 200 cases and cleanup/formatting wording for 30; the repository URL, dataset and bug id are included. The label is directly inferable for at least 200 cases (every description with "fix") and probably more (I did not classify the other 50 descriptions). Do not use it as is. Re-export with blinded codes (below) and a neutral description.

## Definitions
- **Observable difference:** reproducible difference between base and variant in outcome, exception type, side effect (stdout, file writes, globals, argument mutation) or API signature, for an input in the valid domain, within the declared observation boundary O = {outcome, exception, side_effect, api}.
- **Valid input domain:** inputs satisfying the function's documented or evident preconditions; inputs that violate them (or that rely on unspecified behaviour) do not count.
- **Budget B:** at most 45 minutes per case, with the base and variant source, patch diff and the repository's own tests; the reviewer may write new inputs and execute them; no access to any SBG output.
- **Evidence requirement:** CONFIRMED_DIVERGENCE needs a concrete input plus the two observed outputs, reproduced twice.

## Case selection and blinding
1. Fix the case list and seed before reviewing; stratify by dataset, project, change type (neutral to the reviewer).
2. Assign each case a random code `ADJ-xxxxxx` (HMAC of the pair id with a key held by a third party); keep the code map outside the reviewers' reach.
3. Strip: dataset and project names, bug ids, commit hashes, descriptions, test purposes, risk scores, verdicts, ERS output, prediction lock.
4. Include: base and variant source (or checkout), diff, test code, how to run.
5. Reviewers adjudicate **before** the sealed predictions are opened; the lock hash is recorded in the registry.

## Reviewers and process
- Two independent reviewers (A, B) per case, not authors of SBG and not communicating. Reviewer identities and qualifications are recorded in the registry; none are assigned here.
- Disagreement: third reviewer C, unaware of A/B notes, decides. Otherwise the case stays `INDETERMINATE` and enters the estimand as unresolved (complete-case, worst-case, optimistic variants).
- Agreement: Cohen's κ with confusion matrix on all double-labelled cases; scoring may begin only if κ ≥ 0.7 on at least 30% of cases.
- Uncertainty: verdict options `CONFIRMED_DIVERGENCE`, `NO_DIVERGENCE_FOUND_WITHIN_BUDGET`, `INDETERMINATE`; confidence HIGH/MEDIUM/LOW; free-text notes with the witness.
- Registry is append-only and hash-chained; nothing is edited after unblinding.

## Analysis plan (frozen before review)
False-assurance risk among SBG `NO_DIVERGENCE_OBSERVED` verdicts under the three unresolved-case variants, with project-cluster bootstrap; reported against the matched-coverage comparison already in the manuscript.
