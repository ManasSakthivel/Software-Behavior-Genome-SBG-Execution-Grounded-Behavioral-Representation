import unittest

import testutil as T
import obs_points_outfree as OF
import obs_points_outreading as OR


def tr(ret="1", args=None, local=None, fname="f", exc=None, stdout=""):
    w0, w1 = T.wrapper()
    ev = list(w0)
    ev.append(["c", fname, 1, dict(args or {"nums": "[3, 1]", "k": "2"})])
    ev.append(["c", "h", 5, {"v": "3"}])
    ev.append(["r", "h", 6, {"v": "3", "out": "6"}])
    ev.append(["r", fname, 4, dict(local or {"nums": "[3, 1]", "k": "2", "total": "6"})])
    ev += w1
    return {"events": ev, "ret": ret, "exc": exc, "stdout": stdout}


def rec(inps, path, entry="f"):
    return T.rec(None, T.trace_record(inps, entry), path=path)


class Obs(unittest.TestCase):
    def setUp(self):
        self.ctx = T.CTX()
        self.A = rec([tr(), tr()], "A")

    def test_identical_zero(self):
        B = rec([tr(), tr()], "B")
        self.assertEqual(OF.score_pair(self.A, B, self.ctx), 0.0)
        self.assertEqual(OR.score_pair(self.A, B, self.ctx), 0.0)

    def test_rename_invariance(self):
        B = rec([tr(fname="g", args={"items": "[3, 1]", "kk": "2"}, local={"items": "[3, 1]", "kk": "2", "acc": "6"})] * 2, "B", "g")
        self.assertEqual(OF.score_pair(self.A, B, self.ctx), 0.0)
        self.assertEqual(OR.score_pair(self.A, B, self.ctx), 0.0)

    def test_internal_state_change_seen_by_outfree(self):
        B = rec([tr(args={"nums": "[3, 1]", "k": "5"}), tr()], "B")
        self.assertGreater(OF.score_pair(self.A, B, self.ctx), 0.0)

    def test_return_only_change_invisible_to_outfree_visible_to_reading(self):
        B = rec([tr(ret="2"), tr(ret="2")], "B")
        self.assertEqual(OF.score_pair(self.A, B, self.ctx), 0.0)             # output-free: does not read ret
        self.assertGreater(OR.score_pair(self.A, B, self.ctx), 0.0)           # privileged: reads ret
        C = rec([tr(exc="ValueError: x"), tr(stdout="hi")], "C")
        self.assertEqual(OF.score_pair(self.A, C, self.ctx), 0.0)
        self.assertGreater(OR.score_pair(self.A, C, self.ctx), 0.0)

    def test_abstract_locals_ignore_values_but_not_types(self):
        B = rec([tr(local={"nums": "[9, 9]", "k": "7", "total": "99"}), tr()], "B")      # same types / sizes / signs
        self.assertEqual(OF.score_pair_multi(self.A, B, self.ctx)["obs_outfree_abslocals_mean"], 0.0)
        C = rec([tr(local={"nums": "[]", "k": "2", "total": "6"}), tr()], "C")
        self.assertGreater(OF.score_pair_multi(self.A, C, self.ctx)["obs_outfree_abslocals_mean"], 0.0)


if __name__ == "__main__":
    unittest.main()
