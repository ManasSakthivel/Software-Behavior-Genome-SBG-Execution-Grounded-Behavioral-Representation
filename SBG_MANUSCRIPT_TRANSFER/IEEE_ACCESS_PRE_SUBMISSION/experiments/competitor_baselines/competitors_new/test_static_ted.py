import random
import unittest

import testutil as T
import cn_lib as L
import static_ted

SRC = '''
def solve(nums, k):
    """doc"""
    total = 0
    for x in nums:
        if x > k:
            total += x
    return total
'''


class TED(unittest.TestCase):
    def test_zhang_shasha_paper_example(self):
        # Zhang & Shasha 1989 Fig.: f(d(a, c(b)), e)  vs  f(c(d(a, b)), e)  -> distance 2
        leaf = lambda x: (x, [])  # noqa: E731
        t1 = ("f", [("d", [leaf("a"), ("c", [leaf("b")])]), leaf("e")])
        t2 = ("f", [("c", [("d", [leaf("a"), leaf("b")])]), leaf("e")])
        self.assertEqual(static_ted.zhang_shasha(t1, t2), 2)
        self.assertEqual(static_ted.zhang_shasha(t1, t1), 0)
        self.assertEqual(static_ted.zhang_shasha(leaf("a"), leaf("b")), 1)
        self.assertEqual(static_ted.zhang_shasha(("r", [leaf("a")]), ("r", [leaf("a"), leaf("b")])), 1)

    def test_lev_matches_dp(self):
        rnd = random.Random(0)

        def dp(a, b):
            prev = list(range(len(b) + 1))
            for i, x in enumerate(a, 1):
                cur = [i]
                for j, y in enumerate(b, 1):
                    cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
                prev = cur
            return prev[-1]
        for _ in range(300):
            a = [rnd.randint(0, 3) for _ in range(rnd.randint(0, 12))]
            b = [rnd.randint(0, 3) for _ in range(rnd.randint(0, 12))]
            self.assertEqual(L.lev(a, b), dp(a, b))

    def test_identical_and_rename_and_comment(self):
        ctx = T.CTX()
        a = T.rec(SRC)
        self.assertEqual(static_ted.score_pair(a, T.rec(SRC), ctx), 0.0)
        ren = SRC.replace("solve", "fn_zz").replace("nums", "items").replace("total", "acc").replace('"""doc"""', "# comment")
        self.assertEqual(static_ted.score_pair(a, T.rec(ren), ctx), 0.0)           # rename + docstring/comment invariance

    def test_semantic_change_scores_positive(self):
        ctx = T.CTX()
        chg = SRC.replace("x > k", "x >= k")
        s = static_ted.score_pair(T.rec(SRC), T.rec(chg), ctx)
        self.assertGreater(s, 0.0)
        more = SRC.replace("total += x", "total += x\n            total += 1")
        self.assertGreater(static_ted.score_pair(T.rec(SRC), T.rec(more), ctx), 0.0)
        self.assertLess(s, 1.0)

    def test_raw_names_not_invariant(self):
        ctx = T.CTX()
        ren = SRC.replace("total", "acc")
        m = static_ted.score_pair_multi(T.rec(SRC), T.rec(ren), ctx)
        self.assertEqual(m["ted_alpha"], 0.0)
        self.assertGreater(m["ted_raw_names"], 0.0)

    def test_syntax_error_is_nan(self):
        import math
        self.assertTrue(math.isnan(static_ted.score_pair(T.rec(SRC), T.rec("def ("), T.CTX())))


if __name__ == "__main__":
    unittest.main()
