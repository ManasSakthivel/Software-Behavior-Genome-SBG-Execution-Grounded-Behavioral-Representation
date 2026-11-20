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
        if n < 0:
            raise ValueError(f'n must be >= 0, got {n}')
        self._parent: List[int] = list(range(n))
        self._rank: List[int] = [0] * n
        self._n: int = n
        self._components: int = n

    def _validate(self, x: int) -> None:
        if x < 0 or x >= self._n:
            raise IndexError(f'Node {x} out of range [0, {self._n})')

    def find(self, x: int) -> int:
        """Return canonical representative; applies path-compression halving."""
        self._validate(x)
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]
            x = self._parent[x]
        return x

    def union(self, x: int, y: int) -> bool:
        """Merge sets. Returns True if merge happened, False if already same."""
        self._validate(x)
        self._validate(y)
        (rx, ry) = (self.find(x), self.find(y))
        if rx == ry:
            return False
        if self._rank[rx] < self._rank[ry]:
            (rx, ry) = (ry, rx)
        self._parent[ry] = rx
        if self._rank[rx] == self._rank[ry]:
            self._rank[rx] += 1
        self._components -= 1
        return True

    def connected(self, x: int, y: int) -> bool:
        """True iff x and y are in the same component."""
        return self.find(x) == self.find(y)

    def num_components(self) -> int:
        """Number of disjoint components."""
        return self._components

def test_union_find():
    uf_v = UnionFind(5)
    assert uf_v.num_components() == 5
    assert uf_v.union(0, 1) is True
    assert uf_v.num_components() == 4
    assert uf_v.union(0, 1) is False
    assert uf_v.num_components() == 4
    uf_v.union(1, 2)
    uf_v.union(3, 4)
    assert uf_v.connected(0, 2) is True
    assert uf_v.connected(0, 3) is False
    uf_v.union(2, 3)
    assert uf_v.connected(0, 4) is True
    assert uf_v.num_components() == 1
    r_v = uf_v.find(4)
    assert uf_v.find(0) == r_v
    uf0_v = UnionFind(0)
    assert uf0_v.num_components() == 0
    uf1_v = UnionFind(1)
    assert uf1_v.find(0) == 0
    assert uf1_v.num_components() == 1
    uf2_v = UnionFind(3)
    try:
        uf2_v.find(5)
        assert False
    except IndexError:
        pass
    n_v = 100
    ufn_v = UnionFind(n_v)
    for i_v in range(n_v - 1):
        ufn_v.union(i_v, i_v + 1)
    assert ufn_v.num_components() == 1
    assert ufn_v.connected(0, n_v - 1) is True
    uf3_v = UnionFind(6)
    for pair_v in [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]:
        uf3_v.union(*pair_v)
    root_before_v = uf3_v.find(5)
    root_after_v = uf3_v.find(5)
    assert root_before_v == root_after_v
    print('All union-find tests passed.')
if __name__ == '__main__':
    test_union_find()
    uf = UnionFind(7)
    edges = [(0, 1), (1, 2), (3, 4), (5, 6)]
    for (u, v) in edges:
        uf.union(u, v)
    print('Components:', uf.num_components())
    print('0-2 connected:', uf.connected(0, 2))
    print('0-3 connected:', uf.connected(0, 3))