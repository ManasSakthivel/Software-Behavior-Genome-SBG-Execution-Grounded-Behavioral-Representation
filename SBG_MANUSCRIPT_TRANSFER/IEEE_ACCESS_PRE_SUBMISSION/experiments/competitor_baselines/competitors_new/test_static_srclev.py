import math
import unittest

import testutil as T
import static_srclev

SRC = '''
def solve(nums, k):
    """doc"""
    total = 0   # acc
    for x in nums:
        if x > k:
            total += x
    return total
'''


class SrcLev(unittest.TestCase):
    def setUp(self):
        self.ctx = T.CTX()
        self.a = T.rec(SRC)

    def test_identical_zero(self):
        self.assertEqual(static_srclev.score_pair(self.a, T.rec(SRC), self.ctx), 0.0)

    def test_format_comment_rename_invariant(self):
        v = SRC.replace("solve", "zz").replace("nums", "it").replace("total", "acc").replace("# acc", "").replace("x > k", "(x>k)").replace('"""doc"""', "'''other'''")
        self.assertEqual(static_srclev.score_pair(self.a, T.rec(v), self.ctx), 0.0)
        self.assertEqual(static_srclev.score_pair_multi(self.a, T.rec(v), self.ctx)["srclev_unparse"] > 0, True)   # raw-name variant is NOT invariant

    def test_change_positive_and_bounded(self):
        v = SRC.replace("x > k", "x < k")
        s = static_srclev.score_pair(self.a, T.rec(v), self.ctx)
        self.assertTrue(0.0 < s < 1.0)
        self.assertGreater(static_srclev.score_pair(self.a, T.rec(SRC + "\ndef extra(a):\n    return a + 1\n"), self.ctx), 0.0)

    def test_unparse_variant_not_rename_invariant(self):
        m = static_srclev.score_pair_multi(self.a, T.rec(SRC.replace("total", "acc")), self.ctx)
        self.assertEqual(m["srclev_alpha"], 0.0)
        self.assertGreater(m["srclev_unparse"], 0.0)

    def test_nan_on_syntax_error(self):
        self.assertTrue(math.isnan(static_srclev.score_pair(self.a, T.rec("def ("), self.ctx)))


if __name__ == "__main__":
    unittest.main()
