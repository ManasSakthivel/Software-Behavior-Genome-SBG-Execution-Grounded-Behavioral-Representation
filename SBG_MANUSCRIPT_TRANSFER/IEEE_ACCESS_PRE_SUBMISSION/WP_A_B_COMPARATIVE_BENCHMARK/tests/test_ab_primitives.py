"""WP-A/B independent verification tests (EXP-A4R-002).  Tests primitives of the predecessor modules (bl_common, b02_static) and of the A4B
competitor library (cn_lib) against brute-force reference implementations written here, plus label-freeness and held-out-guard static checks.
Read-only on all source modules.  Run:  python -m pytest -p no:cacheprovider WP_A_B_COMPARATIVE_BENCHMARK/tests -q
"""
from __future__ import annotations

import ast
import pathlib
import random
import re
import sys
import unittest

WP = pathlib.Path(__file__).resolve().parents[1]
PKG = WP.parent
CB = PKG / "experiments" / "competitor_baselines"
sys.dont_write_bytecode = True
sys.path[:0] = [str(CB), str(CB / "competitors_new")]
import bl_common as BL  # noqa: E402
import cn_lib as CN  # noqa: E402


def brute_lev(a, b):
    n, m = len(a), len(b)
    T = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        T[i][0] = i
    for j in range(m + 1):
        T[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            T[i][j] = min(T[i - 1][j] + 1, T[i][j - 1] + 1, T[i - 1][j - 1] + (a[i - 1] != b[j - 1]))
    return T[n][m]


def brute_lcs(a, b):
    n, m = len(a), len(b)
    T = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            T[i][j] = T[i - 1][j - 1] + 1 if a[i - 1] == b[j - 1] else max(T[i - 1][j], T[i][j - 1])
    return T[n][m]


def rnd_seqs(rng, n_cases=4000):
    for _ in range(n_cases):
        k = rng.choice([1, 2, 3, 5, 20])
        la, lb = rng.randint(0, 40), rng.randint(0, 40)
        a = [rng.randrange(k) for _ in range(la)]
        if rng.random() < 0.5:  # near-duplicate (the realistic regime: base vs variant traces)
            b = list(a)
            for _ in range(rng.randint(0, 4)):
                op = rng.choice("ids")
                if op == "i":
                    b.insert(rng.randint(0, len(b)), rng.randrange(k))
                elif op == "d" and b:
                    del b[rng.randrange(len(b))]
                elif b:
                    b[rng.randrange(len(b))] = rng.randrange(k)
        else:
            b = [rng.randrange(k) for _ in range(lb)]
        yield a, b


class Primitives(unittest.TestCase):
    def test_lev_lcs_bruteforce(self):
        rng = random.Random(20260114)
        n = 0
        for a, b in rnd_seqs(rng):
            for name, mod in (("bl_common", BL), ("cn_lib", CN)):
                self.assertEqual(mod.lev(a, b), brute_lev(a, b), (name, "lev", a, b))
                self.assertEqual(mod.lcs_len(a, b), brute_lcs(a, b), (name, "lcs", a, b))
            n += 1
        self.assertGreaterEqual(n, 4000)

    def test_lev_long_sequences(self):
        rng = random.Random(7)
        for _ in range(40):
            a = [rng.randrange(6) for _ in range(rng.randint(150, 300))]
            b = list(a)
            for _ in range(rng.randint(1, 12)):
                b.insert(rng.randint(0, len(b)), rng.randrange(6))
            self.assertEqual(BL.lev(a, b), brute_lev(a, b))
            self.assertEqual(CN.lev(a, b), brute_lev(a, b))
            self.assertEqual(BL.lcs_len(a, b), brute_lcs(a, b))
            self.assertEqual(CN.lcs_len(a, b), brute_lcs(a, b))

    def test_string_inputs_and_symmetry(self):
        for a, b in (("kitten", "sitting"), ("", "abc"), ("abc", ""), ("same", "same"), ("flaw", "lawn")):
            self.assertEqual(BL.lev(a, b), brute_lev(a, b))
            self.assertEqual(CN.lev(a, b), brute_lev(a, b))
            self.assertEqual(BL.lev(a, b), BL.lev(b, a))

    def test_norms_bounded(self):
        rng = random.Random(3)
        for a, b in rnd_seqs(rng, 500):
            for f in (BL.lev_norm, CN.lev_norm):
                self.assertTrue(0.0 <= f(a, b) <= 1.0)
            if a or b:
                self.assertTrue(0.0 <= BL.lcs_dist(a, b) <= 1.0)
        self.assertEqual(BL.lev_norm([], []), 0.0)
        self.assertEqual(BL.lcs_dist([], []), 0.0)

    def test_set_distances(self):
        from collections import Counter
        for mod in (BL, CN):
            self.assertEqual(mod.jaccard_dist(set(), set()), 0.0)
            self.assertEqual(mod.jaccard_dist({1, 2}, {2, 3}), 1 - 1 / 3)
            self.assertEqual(mod.wjaccard_dist(Counter(), Counter()), 0.0)
            self.assertAlmostEqual(mod.wjaccard_dist(Counter({"a": 2, "b": 1}), Counter({"a": 1, "b": 3})), 1 - (1 + 1) / (2 + 3))

    def test_first_div(self):
        self.assertEqual(BL.first_div([1, 2, 3], [1, 2, 3]), 0.0)
        self.assertEqual(BL.first_div([], []), 0.0)
        self.assertAlmostEqual(BL.first_div([1, 2, 3, 4], [1, 2, 9, 4]), 1 - 2 / 4)
        self.assertAlmostEqual(BL.first_div([1, 2], [1, 2, 3, 4]), 1 - 2 / 4)   # prefix: divergence at the end of the shorter

    def test_cosine(self):
        self.assertAlmostEqual(BL.cosine_dist({"a": 1.0}, {"a": 2.0}), 0.0)
        self.assertAlmostEqual(BL.cosine_dist({"a": 1.0}, {"b": 1.0}), 1.0)
        self.assertEqual(BL.cosine_dist({}, {}), 0.0)


class Anonymisation(unittest.TestCase):
    def test_full_canon_first_appearance(self):
        ev = [("c", "main", 1, None), ("c", "helper", 2, None), ("r", "helper", 3, None), ("r", "main", 4, None)]
        self.assertEqual(BL.tokens(ev, "main", "call", "full"), ["f0", "f1"])
        ev2 = [("c", "Q", 1, None), ("c", "zz", 2, None), ("r", "zz", 3, None), ("r", "Q", 4, None)]
        self.assertEqual(BL.tokens(ev2, "Q", "call", "full"), BL.tokens(ev, "main", "call", "full"))
        # raw naming is NOT rename-invariant
        self.assertNotEqual(BL.tokens(ev2, "Q", "call", "raw"), BL.tokens(ev, "main", "call", "raw"))


class StaticChecks(unittest.TestCase):
    """Static scans: label / held-out access in score-producing modules."""
    LABEL = re.compile(r"""\[['"]label['"]\]|\.get\(['"]label['"]|\blabels?\b\s*=|\by_true\b|\bgroup\b""")

    def test_new_modules_do_not_read_labels(self):
        mods = ["static_tce", "static_ted", "static_srclev", "static_tfidf", "birthmark_kgram", "trace_align", "obs_points_outfree",
                "obs_points_outreading", "diffexec_same_input", "indep_exec", "cn_lib"]
        for m in mods:
            src = (CB / "competitors_new" / f"{m}.py").read_text()
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.Subscript):
                    s = ast.unparse(node)
                    self.assertNotIn("['label']", s, f"{m}: label access {s}")
                    self.assertNotIn('["label"]', s, f"{m}: label access {s}")
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" and node.args:
                    a0 = node.args[0]
                    if isinstance(a0, ast.Constant) and a0.value in ("label", "labels", "y"):
                        self.fail(f"{m}: .get('{a0.value}')")

    def test_predecessor_feature_modules_do_not_read_labels(self):
        for m in ("bl_common", "b02_static", "b03_execstats", "b04_valuespectra", "b05_pathspectra", "b05_traceseq", "b06_indep_inputs", "features"):
            tree = ast.parse((CB / f"{m}.py").read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Subscript):
                    s = ast.unparse(node)
                    self.assertNotIn("['label']", s, f"{m}: label access {s}")
                    self.assertNotIn('["label"]', s, f"{m}: label access {s}")

    def test_heldout_guards_present(self):
        ra = (CB / "run" / "run_all.py").read_text()
        self.assertIn("BLOCKED: held-out population", ra)
        self.assertIn("frozen_registered", ra)
        rc = (CB / "run" / "run_competitors.py").read_text()
        self.assertIn("BLOCKED", rc)

    def test_sanity_labels_refuses_heldout(self):
        sl = (CB / "competitors_new" / "sanity_labels.py").read_text()
        self.assertIn('ALLOWED = ("v9c_train", "v9c_dev")', sl)
        self.assertIn("REFUSED", sl)


if __name__ == "__main__":
    unittest.main()
