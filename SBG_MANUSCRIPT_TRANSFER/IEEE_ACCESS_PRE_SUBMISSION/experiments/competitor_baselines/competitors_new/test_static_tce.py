import math
import unittest

import testutil as T
import static_tce

SRC = '''
def solve(nums, k):
    """doc"""
    assert k >= 0
    total = 0
    for x in nums:
        if x > k:
            total += helper(x)
    return total

def helper(v):
    return v * 2
'''


class TCE(unittest.TestCase):
    def setUp(self):
        self.ctx = T.CTX()
        self.a = T.rec(SRC)

    def test_identical_is_zero(self):
        self.assertEqual(static_tce.score_pair(self.a, T.rec(SRC), self.ctx), 0.0)

    def test_rename_invariant(self):
        ren = SRC.replace("solve", "q_main").replace("helper", "dbl").replace("nums", "items").replace("total", "acc").replace("x ", "e ").replace(" x", " e").replace("(x)", "(e)")
        self.assertEqual(static_tce.score_pair(self.a, T.rec(ren), self.ctx), 0.0)

    def test_comment_docstring_assert_invariant(self):
        v = SRC.replace('"""doc"""', "# just a comment").replace("    assert k >= 0\n", "")      # -O2 drops asserts and docstrings
        self.assertEqual(static_tce.score_pair(self.a, T.rec(v), self.ctx), 0.0)
        self.assertEqual(static_tce.score_pair_multi(self.a, T.rec(v), self.ctx)["tce_bytecode_O0"], 1.0)   # unoptimised code differs

    def test_semantic_change_detected(self):
        for chg in (SRC.replace("x > k", "x >= k"), SRC.replace("v * 2", "v * 3"), SRC.replace("total += helper(x)", "total += helper(x) + 1")):
            self.assertEqual(static_tce.score_pair(self.a, T.rec(chg), self.ctx), 1.0)
            m = static_tce.score_pair_multi(self.a, T.rec(chg), self.ctx)
            self.assertGreater(m["bytecode_lev_O2"], 0.0)

    def test_constant_folding_equivalence(self):
        v = SRC.replace("v * 2", "v * (1 + 1)")
        self.assertEqual(static_tce.score_pair(self.a, T.rec(v), self.ctx), 0.0)    # CPython folds 1+1 -> TCE-equal

    def test_syntax_error_is_nan(self):
        self.assertTrue(math.isnan(static_tce.score_pair(self.a, T.rec("def ("), self.ctx)))


if __name__ == "__main__":
    unittest.main()
