# program_id: math_fenwick_tree
# category: mathematical_numerical
# spec_version: 1.0

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
            raise ValueError(f"n must be >= 0, got {n}")
        self._n = n
        self._tree = [0] * (n + 1)   # 1-indexed; index 0 unused

    @classmethod
    def from_list(cls, arr: List[int]) -> "FenwickTree":
        """Build in O(n) using the parent-propagation trick."""
        ft = cls(len(arr))
        for i, v in enumerate(arr):
            ft._tree[i + 1] += v
            parent = (i + 1) + ((i + 1) & -(i + 1))
            if parent <= ft._n:
                ft._tree[parent] += ft._tree[i + 1]
        return ft

    def _check(self, i: int) -> None:
        if i < 0 or i >= self._n:
            raise IndexError(f"Index {i} out of range [0, {self._n})")

    def update(self, i: int, delta: int) -> None:
        """Add delta to element at index i (0-indexed)."""
        self._check(i)
        j = i + 1   # convert to 1-indexed
        while j <= self._n:
            self._tree[j] += delta
            j += j & (-j)

    def prefix_sum(self, i: int) -> int:
        """Sum of elements [0..i] inclusive (0-indexed)."""
        self._check(i)
        j = i + 1   # convert to 1-indexed
        s = 0
        while j > 0:
            s += self._tree[j]
            j -= j & (-j)
        return s

    def range_sum(self, l: int, r: int) -> int:
        """Sum of elements [l..r] inclusive (0-indexed)."""
        if l < 0 or r >= self._n:
            raise IndexError(f"Range [{l},{r}] out of bounds")
        if l > r:
            raise ValueError(f"l ({l}) > r ({r})")
        if l == 0:
            return self.prefix_sum(r)
        return self.prefix_sum(r) - self.prefix_sum(l - 1)

    def point_value(self, i: int) -> int:
        """Current value at index i."""
        return self.range_sum(i, i)


# ---------- tests ----------

def test_fenwick_tree():
    # Test 1: empty Fenwick tree
    ft0 = FenwickTree(0)
    # no queries possible

    # Test 2: prefix_sum after updates
    ft = FenwickTree(6)
    for i, v in enumerate([1, 3, 5, 7, 9, 11]):
        ft.update(i, v)
    assert ft.prefix_sum(5) == 36
    assert ft.prefix_sum(2) == 9   # 1+3+5

    # Test 3: range_sum
    assert ft.range_sum(1, 3) == 15   # 3+5+7
    assert ft.range_sum(0, 5) == 36

    # Test 4: point_value
    assert ft.point_value(4) == 9

    # Test 5: update existing element
    ft.update(2, 4)   # index 2: 5 -> 9
    assert ft.point_value(2) == 9
    assert ft.prefix_sum(2) == 13  # 1+3+9

    # Test 6: from_list
    ft2 = FenwickTree.from_list([2, 4, 6, 8, 10])
    assert ft2.prefix_sum(4) == 30
    assert ft2.range_sum(1, 3) == 18   # 4+6+8

    # Test 7: from_list matches manual updates
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    ft3 = FenwickTree.from_list(arr)
    ft4 = FenwickTree(len(arr))
    for i, v in enumerate(arr):
        ft4.update(i, v)
    for i in range(len(arr)):
        assert ft3.prefix_sum(i) == ft4.prefix_sum(i)

    # Test 8: out-of-range raises
    try:
        ft.prefix_sum(10)
        assert False
    except IndexError:
        pass

    # Test 9: negative delta
    ft5 = FenwickTree(3)
    ft5.update(0, 10)
    ft5.update(0, -3)
    assert ft5.point_value(0) == 7

    # Test 10: l > r raises ValueError
    try:
        ft.range_sum(3, 1)
        assert False
    except ValueError:
        pass

    print("All Fenwick tree tests passed.")


if __name__ == "__main__":
    test_fenwick_tree()
    arr = [1, 3, 5, 7, 9, 11]
    ft = FenwickTree.from_list(arr)
    print("prefix_sum(5):", ft.prefix_sum(5))
    print("range_sum(1,4):", ft.range_sum(1, 4))
    ft.update(2, 2)
    print("After update(2,+2), prefix_sum(5):", ft.prefix_sum(5))
