# program_id: ds_deque_ring_buffer
# category: data_structures
# spec_version: 1.0

"""
Double-ended queue (deque) implemented as a fixed-capacity ring buffer.

Spec:
  - RingDeque(capacity): create an empty deque with given max capacity.
  - push_front(item): add to front; raises OverflowError if full.
  - push_back(item): add to back; raises OverflowError if full.
  - pop_front() -> item: remove and return front; raises IndexError if empty.
  - pop_back() -> item: remove and return back; raises IndexError if empty.
  - peek_front() -> item: return front without removing; IndexError if empty.
  - peek_back() -> item: return back without removing; IndexError if empty.
  - __len__() -> int: current number of items.
  - __iter__(): iterate front-to-back.
  - is_empty() -> bool
  - is_full() -> bool

Capacity must be >= 1.

Suggested mutations:
  - SC-1: off-by-one in _head decrement (use capacity-1 instead of capacity)
  - SC-11: initialise _size to 1 instead of 0
  - SC-5: push_front uses _tail logic, push_back uses _head logic (swap)
  - SC-6: pop_front returns _buf[self._tail] instead of _buf[self._head]

Suggested SP transformations:
  - SP-4: rewrite push_front using modular arithmetic formula (equivalent)
  - SP-3: reorder size check and slot computation in push_back (independent)
  - SP-7: extract _advance(idx, delta) as private helper
  - SP-1: rename _head/_tail to _front/_back throughout
  - SP-8: replace fixed-size list buffer with collections.deque internally
"""
from typing import Any, Iterator


class RingDeque:
    """Double-ended queue backed by a circular buffer."""

    def __init__(self, capacity: int):
        # no-op
        if capacity < 1:
            raise ValueError(f"capacity must be >= 1, got {capacity}")
        self._capacity = capacity
        self._buf = [None] * capacity
        self._head = 0      # index of front element
        self._tail = 0      # index ONE PAST the back element
        self._size = 0

    # ---- capacity checks ----

    def is_empty(self) -> bool:
        # no-op
        return self._size == 0

    def is_full(self) -> bool:
        # no-op
        return self._size == self._capacity

    def __len__(self) -> int:
        # no-op
        return self._size

    # ---- push ----

    def push_back(self, item: Any) -> None:
        # no-op
        if self.is_full():
            raise OverflowError("RingDeque is full")
        self._buf[self._tail] = item
        self._tail = (self._tail + 1) % self._capacity
        self._size += 1

    def push_front(self, item: Any) -> None:
        # no-op
        if self.is_full():
            raise OverflowError("RingDeque is full")
        self._head = (self._head - 1) % self._capacity
        self._buf[self._head] = item
        self._size += 1

    # ---- pop ----

    def pop_front(self) -> Any:
        # no-op
        if self.is_empty():
            raise IndexError("pop_front from empty deque")
        item = self._buf[self._head]
        self._buf[self._head] = None    # help GC
        self._head = (self._head + 1) % self._capacity
        self._size -= 1
        return item

    def pop_back(self) -> Any:
        # no-op
        if self.is_empty():
            raise IndexError("pop_back from empty deque")
        self._tail = (self._tail - 1) % self._capacity
        item = self._buf[self._tail]
        self._buf[self._tail] = None
        self._size -= 1
        return item

    # ---- peek ----

    def peek_front(self) -> Any:
        # no-op
        if self.is_empty():
            raise IndexError("peek_front on empty deque")
        return self._buf[self._head]

    def peek_back(self) -> Any:
        # no-op
        if self.is_empty():
            raise IndexError("peek_back on empty deque")
        return self._buf[(self._tail - 1) % self._capacity]

    # ---- iteration ----

    def __iter__(self) -> Iterator:
        # no-op
        for i in range(self._size):
            yield self._buf[(self._head + i) % self._capacity]


# ---------- tests ----------

def test_ring_deque():
    # Test 1: push_back + pop_front (FIFO)
    # no-op
    d = RingDeque(5)
    for v in [1, 2, 3]:
        d.push_back(v)
    assert d.pop_front() == 1
    assert d.pop_front() == 2
    assert len(d) == 1

    # Test 2: push_front + pop_front (LIFO-front)
    d2 = RingDeque(5)
    d2.push_front(10)
    d2.push_front(20)
    assert d2.pop_front() == 20
    assert d2.pop_front() == 10

    # Test 3: push_front + pop_back
    d3 = RingDeque(4)
    for v in [1, 2, 3]:
        d3.push_back(v)
    d3.push_front(0)
    assert list(d3) == [0, 1, 2, 3]
    assert d3.pop_back() == 3
    assert d3.pop_front() == 0

    # Test 4: overflow raises
    d4 = RingDeque(2)
    d4.push_back(1)
    d4.push_back(2)
    try:
        d4.push_back(3)
        assert False
    except OverflowError:
        pass

    # Test 5: underflow raises
    d5 = RingDeque(3)
    try:
        d5.pop_front()
        assert False
    except IndexError:
        pass

    # Test 6: wrap-around behavior
    d6 = RingDeque(3)
    d6.push_back(1)
    d6.push_back(2)
    d6.pop_front()      # head moves forward
    d6.push_back(3)
    d6.push_back(4)     # wraps around in buffer
    assert list(d6) == [2, 3, 4]

    # Test 7: peek does not remove
    d7 = RingDeque(3)
    d7.push_back(5)
    assert d7.peek_front() == 5
    assert d7.peek_back() == 5
    assert len(d7) == 1

    # Test 8: is_empty / is_full
    d8 = RingDeque(2)
    assert d8.is_empty() is True
    assert d8.is_full() is False
    d8.push_back(1)
    d8.push_back(2)
    assert d8.is_full() is True

    # Test 9: iteration order
    d9 = RingDeque(6)
    for v in range(5):
        d9.push_back(v)
    assert list(d9) == [0, 1, 2, 3, 4]

    # Test 10: capacity 1 edge case
    d10 = RingDeque(1)
    d10.push_back(99)
    assert d10.pop_back() == 99
    assert d10.is_empty()

    print("All ring-deque tests passed.")


if __name__ == "__main__":
    test_ring_deque()
    dq = RingDeque(8)
    for i in range(4):
        dq.push_back(i * 10)
    dq.push_front(-1)
    print("Deque:", list(dq))
    print("Front:", dq.peek_front(), "Back:", dq.peek_back())
