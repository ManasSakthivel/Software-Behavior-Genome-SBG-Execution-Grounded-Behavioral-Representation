import math
import unittest

import testutil as T
import cn_lib as L
import static_tfidf

SRC = '''
def solve(nums, k):
    total = 0
    for x in nums:
        if x > k:
            total += x
    return total
'''


def ctx_with_idf():
    ctx = T.CTX()
    docs = [SRC, SRC.replace("x > k", "x < k"), "def g(a):\n    return a\n", "import os\nprint(os.name)\n"]
    ctx._idf = L.fit_idf_tokens(docs)          # stands for the train-only IDF table
    static_tfidf._idf_cache.clear()
    return ctx


class TfIdf(unittest.TestCase):
    def setUp(self):
        self.ctx = ctx_with_idf()
        self.a = T.rec(SRC)

    def test_identical_zero(self):
        self.assertAlmostEqual(static_tfidf.score_pair(self.a, T.rec(SRC), self.ctx), 0.0, places=12)

    def test_identifier_rename_invariant(self):
        v = SRC.replace("solve", "zz").replace("nums", "items").replace("total", "acc").replace(" x ", " e ").replace(" x\n", " e\n")
        self.assertAlmostEqual(static_tfidf.score_pair(self.a, T.rec(v), self.ctx), 0.0, places=12)

    def test_change_positive(self):
        s = static_tfidf.score_pair(self.a, T.rec(SRC.replace("x > k", "x < k")), self.ctx)
        self.assertTrue(0.0 < s < 1.0)
        far = static_tfidf.score_pair(self.a, T.rec("def g(a):\n    return a\n"), self.ctx)
        self.assertGreater(far, s)

    def test_idf_uses_only_given_table(self):
        idf, N = self.ctx.idf_tokens()
        self.assertEqual(N, 4)

    def test_nan_on_empty(self):
        self.assertTrue(math.isnan(static_tfidf.score_pair(T.rec(""), T.rec(""), self.ctx)))


if __name__ == "__main__":
    unittest.main()
