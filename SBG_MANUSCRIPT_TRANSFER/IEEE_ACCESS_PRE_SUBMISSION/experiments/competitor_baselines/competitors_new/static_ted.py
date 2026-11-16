"""static_ted -- Zhang-Shasha tree-edit distance on the alpha-normalised Python AST (class A, source-only, output-free).

Algorithm : Zhang & Shasha (1989) ordered-tree edit distance, unit insert/delete/relabel cost, node label = AST node type + semantic payload
            (alpha-renamed identifier, constant, attribute name, operator via node type).  Docstrings removed, expression-context nodes dropped.
Rename    : program-defined identifiers are alpha-renamed by first appearance => invariant to SP-2-type renaming (default ``rename=True``).
Bounding  : (i) the root's children are stripped of the common prefix/suffix of structurally identical subtrees recursively while the remaining
            single child pair has equal labels (exact for the identical parts, heuristic otherwise); (ii) if the remaining forest pair is larger
            than ``CELL_CAP`` node-pairs the exact ZS is replaced by Levenshtein on the pre-order label sequence (an upper-bound style approximation)
            and the pair is flagged in ``score_pair_multi()['fallback']``.
Score     : TED / (|T_base| + |T_variant|)  in [0, 1]; identical (after normalisation) -> 0.
Status    : ADAPTED (own implementation of a classic algorithm applied to version pairs; no published method for this task).
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cn_lib as L  # noqa: E402

CELL_CAP = 90_000          # |forest1| * |forest2| above which the exact ZS is replaced by the label-sequence Levenshtein


class _Prep:
    def __init__(self, tree):
        self.lab, self.lm = [], []
        self._post(tree)
        n = len(self.lab)
        seen, kr = set(), []
        for i in range(n - 1, -1, -1):           # keyroots: highest index for each distinct leftmost leaf
            if self.lm[i] not in seen:
                seen.add(self.lm[i])
                kr.append(i)
        self.kr = sorted(kr)

    def _post(self, t):
        def rec(node):                     # recursion depth = AST depth (small)
            lml = None
            for c in node[1]:
                l = rec(c)
                if lml is None:
                    lml = l
            idx = len(self.lab)
            self.lab.append(node[0])
            self.lm.append(idx if lml is None else lml)
            return self.lm[idx]
        rec(t)


def zhang_shasha(t1, t2):
    """Exact Zhang-Shasha tree edit distance of two ``(label, [children])`` trees (unit costs)."""
    A, B = _Prep(t1), _Prep(t2)
    n, m = len(A.lab), len(B.lab)
    td = [[0] * m for _ in range(n)]
    for i in A.kr:
        li = A.lm[i]
        for j in B.kr:
            lj = B.lm[j]
            ni, nj = i - li + 2, j - lj + 2
            fd = [[0] * nj for _ in range(ni)]
            for a in range(1, ni):
                fd[a][0] = fd[a - 1][0] + 1
            row0 = fd[0]
            for b in range(1, nj):
                row0[b] = row0[b - 1] + 1
            for a in range(1, ni):
                ia = li + a - 1
                lma = A.lm[ia]
                fa, fp = fd[a], fd[a - 1]
                tdi = td[ia]
                for b in range(1, nj):
                    jb = lj + b - 1
                    if lma == li and B.lm[jb] == lj:
                        c = fp[b - 1] + (0 if A.lab[ia] == B.lab[jb] else 1)
                        v = min(fp[b] + 1, fa[b - 1] + 1, c)
                        fa[b] = v
                        tdi[jb] = v
                    else:
                        v = min(fp[b] + 1, fa[b - 1] + 1, fd[lma - li][B.lm[jb] - lj] + tdi[jb])
                        fa[b] = v
    return td[n - 1][m - 1]


def _preorder(t, out):
    out.append(t[0])
    for c in t[1]:
        _preorder(c, out)
    return out


def _freeze(t):
    """hashable structural identity of a subtree."""
    return (t[0], tuple(_freeze(c) for c in t[1]))


def _reduce_forests(t1, t2):
    """Strip identical prefix/suffix children recursively. Returns (forest1, forest2) -- lists of subtrees -- to be compared under a dummy root."""
    f1, f2 = [t1], [t2]
    while len(f1) == 1 and len(f2) == 1 and f1[0][0] == f2[0][0]:
        c1, c2 = f1[0][1], f2[0][1]
        h1, h2 = [_freeze(c) for c in c1], [_freeze(c) for c in c2]
        p = 0
        while p < len(c1) and p < len(c2) and h1[p] == h2[p]:
            p += 1
        s = 0
        while s < len(c1) - p and s < len(c2) - p and h1[-1 - s] == h2[-1 - s]:
            s += 1
        r1, r2 = c1[p:len(c1) - s], c2[p:len(c2) - s]
        if not r1 and not r2:
            return [], []
        f1, f2 = r1, r2
    return f1, f2


def ted_pair(t1, t2):
    """(ted, size1, size2, fallback_flag)."""
    n1, n2 = L.tree_size(t1), L.tree_size(t2)
    f1, f2 = _reduce_forests(t1, t2)
    if not f1 and not f2:
        return 0, n1, n2, False
    r1, r2 = ("R", f1), ("R", f2)
    s1, s2 = L.tree_size(r1), L.tree_size(r2)
    if s1 * s2 > CELL_CAP:
        a, b = _preorder(r1, []), _preorder(r2, [])
        return L.lev(a, b), n1, n2, True
    return zhang_shasha(r1, r2), n1, n2, False


def _trees(rec, ctx, rename, labels=True):
    src = ctx.source(rec)
    if src is None:
        return None
    try:
        return L.ast_tree(L.parse_normalised(src, rename=rename), labels)
    except SyntaxError:
        return None


def ted_score(base, var, ctx, rename=True, labels=True):
    ta, tb = _trees(base, ctx, rename, labels), _trees(var, ctx, rename, labels)
    if ta is None or tb is None:
        return L.NAN, False, 0
    d, n1, n2, fb = ted_pair(ta, tb)
    return d / (n1 + n2), fb, d


def score_pair(base_record, variant_record, ctx):
    """Default configuration: alpha-renamed, full labels, TED/(|T1|+|T2|)."""
    return ted_score(base_record, variant_record, ctx, True, True)[0]


def score_pair_multi(base_record, variant_record, ctx):
    s, fb, d = ted_score(base_record, variant_record, ctx, True, True)
    s_raw, fb_raw, d_raw = ted_score(base_record, variant_record, ctx, False, True)
    s_ty, fb_ty, d_ty = ted_score(base_record, variant_record, ctx, True, False)
    return {"ted_alpha": s, "ted_raw_names": s_raw, "ted_types_only": s_ty, "ted_alpha_abs": float(d),
            "fallback": float(fb or fb_raw or fb_ty)}
