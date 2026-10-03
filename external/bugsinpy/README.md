# BugsInPy units (external real-program corpus)

Function-level units extracted from the upstream projects that BugsInPy
catalogues. They are used only as external test data for
`experiments/final/external_bugsinpy.py`, and never for development,
threshold selection or weighting.

- **Source catalogue.** https://github.com/soarsmu/BugsInPy at commit `11c5f1eea954a42132cfd06bf257766a7963e0fd`.
- **Upstream code.** Each file was fetched from the project's GitHub repository
  at the exact buggy and fixed commits recorded by BugsInPy, through the GitHub
  contents API. The commits are listed in `manifest.json`. Abbreviated commit
  ids were expanded to full SHAs; the recorded form is kept alongside.
- **Extraction.** Each unit is the changed top-level function, or the class
  containing the changed method, together with its same-file closure. The code
  is copied verbatim. A three-line provenance header is prepended and nothing
  else is edited.
- **Eligibility.** A static rule decides it, before any execution. The rule is
  in the script docstring. Every one of the 501 bugs
  appears in `manifest.json` with its eligibility, or with the reason it was
  excluded.
- **Negatives.** The `neg_sp-*.py` files are this repository's SP transformers
  applied to `fixed.py`, in the pre-registered order with seed 0.
- **Freeze.** `artifacts/final/freeze_bugsinpy.json` holds the SHA-256 of the
  manifest and of every file here. It was written before any unit was
  executed, and the scoring stage refuses to run if any hash differs.

## Licenses

Each unit stays under its upstream project's license. The per-project SPDX
identifiers were read from the GitHub API:

| project | license (GitHub SPDX) | eligible units |
|---|---|---|
| ansible | GPL-3.0 | 6 |
| black | MIT | 3 |
| httpie | BSD-3-Clause | 1 |
| keras | Apache-2.0 | 3 |
| luigi | Apache-2.0 | 4 |
| matplotlib | NOASSERTION | 2 |
| pandas | BSD-3-Clause | 3 |
| scrapy | BSD-3-Clause | 4 |
| spacy | MIT | 4 |
| thefuck | MIT | 7 |
| tqdm | NOASSERTION | 1 |
| youtube-dl | Unlicense | 17 |

`NOASSERTION` means GitHub could not classify the license file. Consult the
upstream repository.

**License note: ansible units.** Ansible is GPL-3.0. Those units are
distributed here under GPL-3.0, separately from the rest of this repository.

## Rebuild

```
python experiments/final/external_bugsinpy.py fetch --bugsinpy-dir <BugsInPy checkout> --cache-dir <cache>
python experiments/final/external_bugsinpy.py build --cache-dir <cache>
python experiments/final/external_bugsinpy.py score --protocol output_free_v7
```

The `score` stage needs only the vendored files. `fetch` needs an
authenticated `gh` CLI.
