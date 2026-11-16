import math
import unittest

import testutil as T
import birthmark_kgram as BK


def tr(names):
    return T.call_trace(names)


def rec_for(seqs, path):
    return T.rec(None, T.trace_record([tr(s) for s in seqs], "m"), path=path)


class Birthmark(unittest.TestCase):
    def setUp(self):
        self.ctx = T.CTX()
        self.seqs = [["m", "a", "b", "a", "b", "c"], ["m", "a", "a", "c", "b"]]
        self.A = rec_for(self.seqs, "A")

    def test_identical_zero(self):
        self.assertEqual(BK.score_pair(self.A, rec_for(self.seqs, "A2"), self.ctx), 0.0)
        self.assertTrue(all(v == 0.0 for v in BK.score_pair_multi(self.A, rec_for(self.seqs, "A3"), self.ctx).values()))

    def test_rename_invariance_anon_only(self):
        ren = {"m": "main", "a": "alpha", "b": "beta", "c": "gamma"}
        B = rec_for([[ren[x] for x in s] for s in self.seqs], "B")
        self.assertEqual(BK.score_pair(self.A, B, self.ctx), 0.0)
        m = BK.score_pair_multi(self.A, B, self.ctx)
        self.assertEqual(m["birthmark_k3_jaccard_anon"], 0.0)
        self.assertEqual(m["birthmark_k3_jaccard_raw"], 1.0)

    def test_change_detected_and_graded(self):
        one = rec_for([["m", "a", "b", "a", "b", "c"], ["m", "a", "a", "c", "c"]], "C")        # last element differs
        s_small = BK.score_pair_multi(self.A, one, self.ctx)["birthmark_k2_jaccard_anon"]
        many = rec_for([["m", "c", "c", "c", "c", "c"], ["m", "b", "b", "b", "b"]], "D")
        s_big = BK.score_pair_multi(self.A, many, self.ctx)["birthmark_k2_jaccard_anon"]
        self.assertTrue(0.0 < s_small < s_big <= 1.0)

    def test_containment_symmetric_and_subset(self):
        sub = rec_for([["m", "a"]], "S")
        m = BK.score_pair_multi(self.A, sub, self.ctx)
        self.assertGreater(m["birthmark_k2_containment_anon"], 0.0)                   # sub is contained in A but A is not in sub -> still different

    def test_missing_trace_nan(self):
        self.assertTrue(math.isnan(BK.score_pair(self.A, T.rec(None, path="zz", base_id="__none__"), self.ctx)))


if __name__ == "__main__":
    unittest.main()
