# program_id: algo_segment_tree
# category: data_structures
# spec_version: 1.0

"""
Segment Tree with lazy propagation for range-sum queries and range-add updates.

Spec:
  - SegmentTree(arr): build from a list of integers in O(n).
  - query(l, r) -> int: return sum of arr[l..r] (inclusive, 0-indexed).
  - update(l, r, delta): add delta to every element in arr[l..r].
  - point_query(i) -> int: return current value at index i.
  - to_list() -> list: materialise current array state.

Raises IndexError for out-of-range l, r, or i.
Raises ValueError if l > r.

Lazy propagation: pending additions are pushed down only when a node must be
subdivided. The tree is built on 1-based internal nodes; the public API is
0-indexed.

Suggested mutations:
  - SC-1: off-by-one in push_down — propagate to one child only
  - SC-9: omit lazy propagation in update (correct range update but wrong query)
  - SC-2: use product instead of sum in build/query
  - SC-11: initialise lazy array to 1 instead of 0

Suggested SP transformations:
  - SP-4: convert recursive build to iterative (bottom-up) build
  - SP-7: extract _push_down into standalone helper accepting tree + lazy arrays
  - SP-3: reorder tree[node] and size computation in build (independent lines)
  - SP-1: rename internal node index variable from `node` to `v`
  - SP-9: replace with a Fenwick tree (BIT) for sum-only queries (equivalent
          when updates are point updates; not equivalent for range-add)
"""
from typing import List


class SegmentTree:
    """Range-sum segment tree with range-add lazy propagation."""

    def __init__(self, arr: List[int]):
        self._n = len(arr)
        self._tree = [0] * (4 * self._n)
        self._lazy = [0] * (4 * self._n)
        if self._n > 0:
            self._build(arr, 1, 0, self._n - 1)

    def _build(self, arr: List[int], node: int, start: int, end: int) -> None:
        if start == end:
            self._tree[node] = arr[start]
            return
        mid = (start + end) // 2
        self._build(arr, 2 * node, start, mid)
        self._build(arr, 2 * node + 1, mid + 1, end)
        self._tree[node] = self._tree[2 * node] + self._tree[2 * node + 1]

    def _push_down(self, node: int, start: int, end: int) -> None:
        if self._lazy[node] != 0:
            mid = (start + end) // 2
            left, right = 2 * node, 2 * node + 1
            # propagate to children
            self._tree[left] += self._lazy[node] * (mid - start + 1)
            self._lazy[left] += self._lazy[node]
            self._tree[right] += self._lazy[node] * (end - mid)
            self._lazy[right] += self._lazy[node]
            self._lazy[node] = 0

    def _update(self, node: int, start: int, end: int,
                 l: int, r: int, delta: int) -> None:
        if r < start or end < l:
            return
        if l <= start and end <= r:
            self._tree[node] += delta * (end - start + 1)
            self._lazy[node] += delta
            return
        self._push_down(node, start, end)
        mid = (start + end) // 2
        self._update(2 * node, start, mid, l, r, delta)
        self._update(2 * node + 1, mid + 1, end, l, r, delta)
        self._tree[node] = self._tree[2 * node] + self._tree[2 * node + 1]

    def _query(self, node: int, start: int, end: int, l: int, r: int) -> int:
        if r < start or end < l:
            return 0
        if l <= start and end <= r:
            return self._tree[node]
        self._push_down(node, start, end)
        mid = (start + end) // 2
        return (self._query(2 * node, start, mid, l, r) +
                self._query(2 * node + 1, mid + 1, end, l, r))

    def _check_range(self, l: int, r: int) -> None:
        if l < 0 or r >= self._n:
            raise IndexError(f"Range [{l},{r}] out of bounds for n={self._n}")
        if l > r:
            raise ValueError(f"l ({l}) must be <= r ({r})")

    def query(self, l: int, r: int) -> int:
        self._check_range(l, r)
        return self._query(1, 0, self._n - 1, l, r)

    def update(self, l: int, r: int, delta: int) -> None:
        self._check_range(l, r)
        self._update(1, 0, self._n - 1, l, r, delta)

    def point_query(self, i: int) -> int:
        if i < 0 or i >= self._n:
            raise IndexError(f"Index {i} out of bounds for n={self._n}")
        return self.query(i, i)

    def to_list(self) -> List[int]:
        return [self.point_query(i) for i in range(self._n)]


# ---------- tests ----------

def test_segment_tree():
    # Test 1: basic range sum
    st = SegmentTree([1, 3, 5, 7, 9, 11])
    assert st.query(0, 5) == 36
    assert st.query(1, 3) == 15   # 3+5+7
    assert st.query(2, 2) == 5

    # Test 2: point query
    assert st.point_query(4) == 9

    # Test 3: range update + requery
    st.update(1, 3, 2)   # add 2 to indices 1,2,3
    assert st.query(1, 3) == 21   # 5+7+9
    assert st.query(0, 5) == 42   # original 36 + 3*2

    # Test 4: overlapping queries after update
    assert st.point_query(0) == 1   # unchanged
    assert st.point_query(4) == 9   # unchanged

    # Test 5: full range update
    st2 = SegmentTree([0, 0, 0, 0])
    st2.update(0, 3, 5)
    assert st2.query(0, 3) == 20
    assert st2.to_list() == [5, 5, 5, 5]

    # Test 6: nested updates
    st3 = SegmentTree([1, 2, 3, 4, 5])
    st3.update(0, 4, 1)   # all +1: [2,3,4,5,6]
    st3.update(2, 4, 3)   # indices 2-4 +3: [2,3,7,8,9]
    assert st3.to_list() == [2, 3, 7, 8, 9]
    assert st3.query(0, 4) == 29

    # Test 7: empty tree
    st_empty = SegmentTree([])
    # no query possible; just verify construction

    # Test 8: single element
    st1 = SegmentTree([42])
    assert st1.query(0, 0) == 42
    st1.update(0, 0, 8)
    assert st1.query(0, 0) == 50

    # Test 9: out-of-range raises
    st4 = SegmentTree([1, 2, 3])
    try:
        st4.query(0, 5)
        assert False
    except IndexError:
        pass

    # Test 10: l > r raises ValueError
    try:
        st4.query(2, 1)
        assert False
    except ValueError:
        pass

    print("All segment tree tests passed.")


if __name__ == "__main__":
    test_segment_tree()
    arr = [1, 3, 5, 7, 9, 11]
    st = SegmentTree(arr)
    print("Initial:", st.to_list())
    st.update(1, 4, 10)
    print("After update(1,4,+10):", st.to_list())
    print("query(0,5):", st.query(0, 5))
