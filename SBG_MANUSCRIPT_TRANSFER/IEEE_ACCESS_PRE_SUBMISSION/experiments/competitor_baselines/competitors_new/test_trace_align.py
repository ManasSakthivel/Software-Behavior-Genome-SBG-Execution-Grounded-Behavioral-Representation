import math
import unittest

import testutil as T
import cn_lib as L
import trace_align

SRC_A = "def f(x):\n    y = x + 1\n    z = helper(y)\n    return z\n\ndef helper(v):\n    return v * 2\n"
# same program, renamed identifiers, comment lines inserted (line numbers shift by 2), different formatting
SRC_B = "# c1\n# c2\ndef g(a):\n    b = a+1\n    c = aux(b)\n    return c\n\ndef aux(w):\n    return w * 2\n"


def tr(rows):
    """rows: list of (type, fn, line)."""
    w0, w1 = T.wrapper()
    return {"events": list(w0) + [[t, f, l, None] for t, f, l in rows] + list(w1), "ret": "1", "exc": None, "stdout": ""}


def trace_a():
    return tr([("c", "f", 1), ("l", "f", 2), ("l", "f", 3), ("c", "helper", 6), ("l", "helper", 7), ("r", "helper", 7), ("l", "f", 4), ("r", "f", 4)])


def trace_b(shift=2):
    return tr([("c", "g", 1 + shift), ("l", "g", 2 + shift), ("l", "g", 3 + shift), ("c", "aux", 6 + shift), ("l", "aux", 7 + shift), ("r", "aux", 7 + shift),
               ("l", "g", 4 + shift), ("r", "g", 4 + shift)])


class Align(unittest.TestCase):
    def setUp(self):
        self.ctx = T.CTX()
        self.A = T.rec(SRC_A, T.trace_record([trace_a(), trace_a()], "f"), path="a.py")
        self.B = T.rec(SRC_B, T.trace_record([trace_b(), trace_b()], "g"), path="b.py")

    def test_identical_zero(self):
        A2 = T.rec(SRC_A, T.trace_record([trace_a(), trace_a()], "f"), path="a2.py")
        self.assertEqual(trace_align.score_pair(self.A, A2, self.ctx), 0.0)

    def test_rename_and_line_shift_invariant_robust_only(self):
        m = trace_align.score_pair_multi(self.A, self.B, self.ctx)
        self.assertEqual(m["align_robust_mean"], 0.0)
        self.assertEqual(trace_align.score_pair(self.A, self.B, self.ctx), 0.0)
        self.assertEqual(m["align_naive_mean"], 1.0)                      # naive tokens share nothing

    def test_behavioural_change_detected(self):
        tc = tr([("c", "f", 1), ("l", "f", 2), ("l", "f", 4), ("r", "f", 4)])          # helper call skipped
        C = T.rec(SRC_A, T.trace_record([tc, tc], "f"), path="c.py")
        s = trace_align.score_pair(self.A, C, self.ctx)
        self.assertTrue(0.0 < s < 1.0)

    def test_unmatched_fraction_and_lcs(self):
        self.assertEqual(L.lcs_len("abcde", "ace"), 3)
        self.assertEqual(L.unmatched_fraction("abc", "abc"), 0.0)
        self.assertAlmostEqual(L.unmatched_fraction("abc", "abd"), 1 - 2 * 2 / 6)

    def test_missing_trace_nan(self):
        miss = T.rec(SRC_A, path="nope.py", pop="v9c_dev", base_id="__none__")
        self.assertTrue(math.isnan(trace_align.score_pair(self.A, miss, self.ctx)))


if __name__ == "__main__":
    unittest.main()
