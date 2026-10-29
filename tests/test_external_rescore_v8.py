"""Regression tests for the corrected external-corpus harness (rescore_external_v8).

Defects covered (artifacts/paper_evidence/DIAGNOSTIC_EXTERNAL.json):
  * `re` compiled-pattern cache makes event counts depend on extraction order;
  * an SP-2 rename of the entry function was scored as a behaviour change.
"""
from __future__ import annotations

import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

REGEX_PROGRAM = '''\
import re

def normalise(text):
    text = re.sub(r"\\s+", " ", text)
    text = re.sub(r"[^a-z ]", "", text.lower())
    return text.strip()
'''

SUM_PROGRAM = '''\
def total(values):
    acc = 0
    for v in values:
        acc += v
    return acc
'''


def _write(tmp_path, name, src):
    p = tmp_path / name
    p.write_text(src)
    return p


def _score(base, variant, protocol=None):
    from experiments.final import extraction as ex
    from experiments.final.rescore_external_v8 import PROTOCOL
    protocol = protocol or PROTOCOL
    a = ex.extract_program(str(base), {}, protocol)
    b = ex.extract_program(str(variant), {}, protocol)
    assert a.ok and b.ok, (a.failure_kind, b.failure_kind)
    return ex.score_pair(a, b)


def test_purged_extraction_is_order_independent(tmp_path):
    """Extracting the same regex-using file twice, cold each time, is identical."""
    from experiments.final.rescore_external_v8 import purged_extract
    path = _write(tmp_path, "regex_prog.py", REGEX_PROGRAM)
    first = purged_extract(str(path))
    # Warm the cache with unrelated work, then extract again (still purged first).
    re.compile(r"\s+")
    re.sub(r"[^a-z ]", "", "warm cache")
    second = purged_extract(str(path))
    assert first.ok and second.ok
    assert first.stats["n_events"] == second.stats["n_events"]


def test_entry_rename_is_not_a_behaviour_change_under_v8(tmp_path):
    """SP-2-style rename of the only function: v8 entry policy scores ~0."""
    base = _write(tmp_path, "base.py", SUM_PROGRAM)
    renamed = _write(tmp_path, "renamed.py",
                     SUM_PROGRAM.replace("total", "renamed_fn_x").replace("values", "vals"))
    scores = _score(base, renamed)
    assert scores["sbg_v5"] == 0.0, scores


def test_genuine_behaviour_change_remains_detectable(tmp_path):
    """The rename fix must not blind the detector to a real change."""
    base = _write(tmp_path, "base.py", SUM_PROGRAM)
    changed = _write(tmp_path, "changed.py", SUM_PROGRAM.replace("acc += v", "acc += v * v"))
    renamed_only = _write(tmp_path, "renamed.py", SUM_PROGRAM.replace("total", "other_name"))
    assert _score(base, changed)["sbg_v5"] > _score(base, renamed_only)["sbg_v5"]


def test_v7_entry_identity_is_name_based_but_v8_is_structural(tmp_path):
    """The entry identity recorded under v7 embeds the function name (so a rename
    changes it); under v8 it is name-free and identical across the rename."""
    from experiments.final import extraction as ex
    base = _write(tmp_path, "base.py", SUM_PROGRAM)
    renamed = _write(tmp_path, "renamed.py", SUM_PROGRAM.replace("total", "renamed_fn_x"))
    a7, b7 = (ex.extract_program(str(p), {}, "output_free_v7") for p in (base, renamed))
    a8, b8 = (ex.extract_program(str(p), {}, "output_free_v8") for p in (base, renamed))
    assert a7.entry_discovery != b7.entry_discovery
    assert a8.entry_discovery == b8.entry_discovery
