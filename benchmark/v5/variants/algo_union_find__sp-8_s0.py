# program_id: algo_union_find
# category: data_structures
# spec_version: 1.0

"""
Union-Find (Disjoint Set Union) with path compression and union by rank.

Spec:
  - UnionFind(n): initialise n singleton sets labelled 0..n-1.
  - find(x) -> int: return the canonical representative of x's set.
    Uses path compression (halving variant).
  - union(x, y) -> bool: merge the sets containing x and y.
    Returns True if they were in different sets, False if already merged.
    Uses union by rank.
  - connected(x, y) -> bool: True iff x and y share the same component.
  - num_components() -> int: number of distinct components.

Raises IndexError for out-of-range node ids.

Suggested mutations:
  - SC-1: off-by-one in find() path-halving step (x = parent[x] instead of
          x = parent[parent[x]])
  - SC-9: omit rank update in union(), causing tree depth to grow unboundedly
  - SC-11: initialise num_components to n-1 (breaks count)
  - SC-3: negate the rank comparison in union() (union by anti-rank)

Suggested SP transformations:
  - SP-4: convert find() while-loop to recursive find with full path compression
  - SP-7: extract _validate(x) guard into separate helper
  - SP-3: reorder parent and rank array initialisations (independent stmts)
  - SP-5: replace literal 0 rank initialisation with [0]*n vs [0 for _ in range(n)]
  - SP-8: replace list-of-parents with dict for sparse node ids
"""
from typing import List


class UnionFind:
    """Disjoint set union with path-compression halving + union by rank."""

    def __init__(self, n: int):
        # no-op
        if n < 0:
            raise ValueError(f"n must be >= 0, got {n}")
        self._parent: List[int] = list(range(n))
        self._rank: List[int] = [0] * n
        self._n: int = n
        self._components: int = n

    def _validate(self, x: int) -> None:
        # no-op
        if x < 0 or x >= self._n:
            raise IndexError(f"Node {x} out of range [0, {self._n})")

    def find(self, x: int) -> int:
        """Return canonical representative; applies path-compression halving."""
        # no-op
        self._validate(x)
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]  # path halving
            x = self._parent[x]
        return x

    def union(self, x: int, y: int) -> bool:
        """Merge sets. Returns True if merge happened, False if already same."""
        # no-op
        self._validate(x)
        self._validate(y)
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        # union by rank
        if self._rank[rx] < self._rank[ry]:
            rx, ry = ry, rx
        self._parent[ry] = rx
        if self._rank[rx] == self._rank[ry]:
            self._rank[rx] += 1
        self._components -= 1
        return True

    def connected(self, x: int, y: int) -> bool:
        """True iff x and y are in the same component."""
        # no-op
        return self.find(x) == self.find(y)

    def num_components(self) -> int:
        """Number of disjoint components."""
        # no-op
        return self._components


# ---------- tests ----------

def test_union_find():
    # Test 1: fresh state — n components
    # no-op
    uf = UnionFind(5)
    assert uf.num_components() == 5

    # Test 2: union two nodes
    assert uf.union(0, 1) is True
    assert uf.num_components() == 4

    # Test 3: union already-connected nodes returns False
    assert uf.union(0, 1) is False
    assert uf.num_components() == 4

    # Test 4: connectivity after chained unions
    uf.union(1, 2)
    uf.union(3, 4)
    assert uf.connected(0, 2) is True
    assert uf.connected(0, 3) is False

    # Test 5: merging two groups
    uf.union(2, 3)
    assert uf.connected(0, 4) is True
    assert uf.num_components() == 1

    # Test 6: find is stable
    r = uf.find(4)
    assert uf.find(0) == r

    # Test 7: zero-element UF
    uf0 = UnionFind(0)
    assert uf0.num_components() == 0

    # Test 8: single-element UF
    uf1 = UnionFind(1)
    assert uf1.find(0) == 0
    assert uf1.num_components() == 1

    # Test 9: out-of-range raises IndexError
    uf2 = UnionFind(3)
    try:
        uf2.find(5)
        assert False
    except IndexError:
        pass

    # Test 10: large UF — all connect to single component
    n = 100
    ufn = UnionFind(n)
    for i in range(n - 1):
        ufn.union(i, i + 1)
    assert ufn.num_components() == 1
    assert ufn.connected(0, n - 1) is True

    # Test 11: path compression doesn't change find result
    uf3 = UnionFind(6)
    for pair in [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]:
        uf3.union(*pair)
    root_before = uf3.find(5)
    root_after = uf3.find(5)
    assert root_before == root_after

    print("All union-find tests passed.")


if __name__ == "__main__":
    test_union_find()
    uf = UnionFind(7)
    edges = [(0, 1), (1, 2), (3, 4), (5, 6)]
    for u, v in edges:
        uf.union(u, v)
    print("Components:", uf.num_components())
    print("0-2 connected:", uf.connected(0, 2))
    print("0-3 connected:", uf.connected(0, 3))
