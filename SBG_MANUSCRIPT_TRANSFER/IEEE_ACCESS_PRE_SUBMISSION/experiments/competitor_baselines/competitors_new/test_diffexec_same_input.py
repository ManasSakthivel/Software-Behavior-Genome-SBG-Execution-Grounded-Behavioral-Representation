import unittest

import testutil as T
import diffexec_same_input as D


def tr(ret="1", exc=None, stdout="", post="[1, 2]", fname="f", pname="xs"):
    w0, w1 = T.wrapper()
    ev = list(w0) + [["c", fname, 1, {pname: "[2, 1]"}], ["r", fname, 3, {pname: post, "tmp": "0"}]] + w1
    return {"events": ev, "ret": ret, "exc": exc, "stdout": stdout}


def rec(inps, path, entry="f"):
    return T.rec(None, T.trace_record(inps, entry), path=path)


class SameInput(unittest.TestCase):
    def setUp(self):
        self.ctx = T.CTX()
        self.A = rec([tr(), tr(ret="2"), tr(ret="3"), tr(ret="4")], "A")

    def test_identical_zero(self):
        self.assertEqual(D.score_pair(self.A, rec([tr(), tr(ret="2"), tr(ret="3"), tr(ret="4")], "B"), self.ctx), 0.0)

    def test_rename_invariance(self):
        B = rec([tr(fname="g", pname="vals"), tr(ret="2", fname="g", pname="vals"), tr(ret="3", fname="g", pname="vals"), tr(ret="4", fname="g", pname="vals")], "B", "g")
        self.assertEqual(D.score_pair(self.A, B, self.ctx), 0.0)

    def test_fraction_and_soft_tiebreak(self):
        B = rec([tr(ret="9"), tr(ret="2"), tr(ret="3"), tr(ret="4")], "B")
        C = rec([tr(ret="10"), tr(ret="2"), tr(ret="3"), tr(ret="4")], "C")
        m = D.score_pair_multi(self.A, B, self.ctx)
        self.assertEqual(m["frac_hard"], 0.25)
        self.assertEqual(m["any_hard"], 1.0)
        self.assertGreater(D.score_pair(self.A, B, self.ctx), D.score_pair(self.A, C, self.ctx))      # graded: 1->9 is a larger repr change than 1->10
        self.assertEqual(D.score_pair_multi(self.A, C, self.ctx)["frac_hard"], 0.25)
        self.assertLess(D.score_pair(self.A, B, self.ctx), 0.25 + 0.0011)

    def test_exception_stdout_and_mutation(self):
        for var, expect in ((tr(exc="ValueError: boom"), 1), (tr(stdout="hello"), 1), (tr(post="[2, 1]"), 1)):       # post-call arg differs = mutation
            B = rec([var, tr(ret="2"), tr(ret="3"), tr(ret="4")], "B")
            self.assertEqual(D.score_pair_multi(self.A, B, self.ctx)["frac_hard"], 0.25)

    def test_changeguard_ignores_same_unintended_exception_message(self):
        a = rec([tr(exc="TypeError: a")], "A")
        b = rec([tr(exc="TypeError: different text")], "B")
        m = D.score_pair_multi(a, b, self.ctx)
        self.assertEqual(m["changeguard_cmp"], 0.0)
        self.assertEqual(m["frac_hard"], 1.0)                                                                       # raw comparator sees the message
        c = rec([tr(exc="AssertionError: x")], "C")
        self.assertEqual(D.score_pair_multi(a, c, self.ctx)["changeguard_cmp"], 1.0)


if __name__ == "__main__":
    unittest.main()
