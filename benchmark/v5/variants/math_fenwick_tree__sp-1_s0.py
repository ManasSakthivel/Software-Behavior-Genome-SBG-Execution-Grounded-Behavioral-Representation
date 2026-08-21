"""
Fenwick Tree (Binary Indexed Tree) for prefix sums and point updates.

Spec:
  - FenwickTree(n): initialise with n zero-valued elements (1-indexed internally).
  - update(i, delta): add delta to element at index i (0-indexed public API).
  - prefix_sum(i) -> int: sum of elements arr[0..i] inclusive (0-indexed).
  - range_sum(l, r) -> int: sum of elements arr[l..r] inclusive.
  - point_value(i) -> int: current value at index i.
  - from_list(arr) -> FenwickTree: class method to build from a list in O(n).

Raises IndexError for out-of-range queries.

The tree uses 1-indexed internal storage; all public methods are 0-indexed.

Suggested mutations:
  - SC-1: off-by-one in prefix_sum — use i instead of i+1 in internal query
  - SC-2: use i & (i-1) instead of i + (i & -i) in update (wrong bit trick)
  - SC-11: initialise internal tree to all-ones instead of zeros
  - SC-6: return _query(l) - _query(r) instead of _query(r) - _query(l-1) in range_sum

Suggested SP transformations:
  - SP-7: extract _internal_query(i) as a named method (currently inline)
  - SP-4: replace while loop with for loop over bit positions
  - SP-3: reorder self._n and self._tree initialisations
  - SP-8: replace with a prefix-sum array (valid SP for sum-only read-heavy use)
  - SP-5: replace i + (i & -i) with i + (i & (-i)) — parenthesisation no-op
"""
from typing import List

class FenwickTree:
    """Binary Indexed Tree for prefix-sum and point-update queries."""

    def __init__(self, n: int):
        if n < 0:
            raise ValueError(f'n must be >= 0, got {n}')
        self._n = n
        self._tree = [0] * (n + 1)

    @classmethod
    def from_list(cls, arr: List[int]) -> 'FenwickTree':
        """Build in O(n) using the parent-propagation trick."""
        ft_v = cls(len(arr))
        for (i, v) in enumerate(arr):
            ft_v._tree[i + 1] += v
            parent_v = i + 1 + (i + 1 & -(i + 1))
            if parent_v <= ft_v._n:
                ft_v._tree[parent_v] += ft_v._tree[i + 1]
        return ft_v

    def _check(self, i: int) -> None:
        if i < 0 or i >= self._n:
            raise IndexError(f'Index {i} out of range [0, {self._n})')

    def update(self, i: int, delta: int) -> None:
        """Add delta to element at index i (0-indexed)."""
        self._check(i)
        j_v = i + 1
        while j_v <= self._n:
            self._tree[j_v] += delta
            j_v += j_v & -j_v

    def prefix_sum(self, i: int) -> int:
        """Sum of elements [0..i] inclusive (0-indexed)."""
        self._check(i)
        j_v = i + 1
        s_v = 0
        while j_v > 0:
            s_v += self._tree[j_v]
            j_v -= j_v & -j_v
        return s_v

    def range_sum(self, l: int, r: int) -> int:
        """Sum of elements [l..r] inclusive (0-indexed)."""
        if l < 0 or r >= self._n:
            raise IndexError(f'Range [{l},{r}] out of bounds')
        if l > r:
            raise ValueError(f'l ({l}) > r ({r})')
        if l == 0:
            return self.prefix_sum(r)
        return self.prefix_sum(r) - self.prefix_sum(l - 1)

    def point_value(self, i: int) -> int:
        """Current value at index i."""
        return self.range_sum(i, i)

def test_fenwick_tree():
    ft0_v = FenwickTree(0)
    ft_v = FenwickTree(6)
    for (i_v, v) in enumerate([1, 3, 5, 7, 9, 11]):
        ft_v.update(i_v, v)
    assert ft_v.prefix_sum(5) == 36
    assert ft_v.prefix_sum(2) == 9
    assert ft_v.range_sum(1, 3) == 15
    assert ft_v.range_sum(0, 5) == 36
    assert ft_v.point_value(4) == 9
    ft_v.update(2, 4)
    assert ft_v.point_value(2) == 9
    assert ft_v.prefix_sum(2) == 13
    ft2_v = FenwickTree.from_list([2, 4, 6, 8, 10])
    assert ft2_v.prefix_sum(4) == 30
    assert ft2_v.range_sum(1, 3) == 18
    arr_v = [3, 1, 4, 1, 5, 9, 2, 6]
    ft3_v = FenwickTree.from_list(arr_v)
    ft4_v = FenwickTree(len(arr_v))
    for (i_v, v) in enumerate(arr_v):
        ft4_v.update(i_v, v)
    for i_v in range(len(arr_v)):
        assert ft3_v.prefix_sum(i_v) == ft4_v.prefix_sum(i_v)
    try:
        ft_v.prefix_sum(10)
        assert False
    except IndexError:
        pass
    ft5_v = FenwickTree(3)
    ft5_v.update(0, 10)
    ft5_v.update(0, -3)
    assert ft5_v.point_value(0) == 7
    try:
        ft_v.range_sum(3, 1)
        assert False
    except ValueError:
        pass
    print('All Fenwick tree tests passed.')
if __name__ == '__main__':
    test_fenwick_tree()
    arr = [1, 3, 5, 7, 9, 11]
    ft = FenwickTree.from_list(arr)
    print('prefix_sum(5):', ft.prefix_sum(5))
    print('range_sum(1,4):', ft.range_sum(1, 4))
    ft.update(2, 2)
    print('After update(2,+2), prefix_sum(5):', ft.prefix_sum(5))