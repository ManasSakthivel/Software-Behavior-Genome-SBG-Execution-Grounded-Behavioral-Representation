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
        if capacity < 1:
            raise ValueError(f'capacity must be >= 1, got {capacity}')
        self._capacity = capacity
        self._buf = [None] * capacity
        self._head = 0
        self._tail = 0
        self._size = 0

    def is_empty(self) -> bool:
        return self._size == 0

    def is_full(self) -> bool:
        return self._size == self._capacity

    def __len__(self) -> int:
        return self._size

    def push_back(self, item: Any) -> None:
        if self.is_full():
            raise OverflowError('RingDeque is full')
        self._buf[self._tail] = item
        self._tail = (self._tail + 1) % self._capacity
        self._size += 1

    def push_front(self, item: Any) -> None:
        if self.is_full():
            raise OverflowError('RingDeque is full')
        self._head = (self._head - 1) % self._capacity
        self._buf[self._head] = item
        self._size += 1

    def pop_front(self) -> Any:
        if self.is_empty():
            raise IndexError('pop_front from empty deque')
        item_v = self._buf[self._head]
        self._buf[self._head] = None
        self._head = (self._head + 1) % self._capacity
        self._size -= 1
        return item_v

    def pop_back(self) -> Any:
        if self.is_empty():
            raise IndexError('pop_back from empty deque')
        self._tail = (self._tail - 1) % self._capacity
        item_v = self._buf[self._tail]
        self._buf[self._tail] = None
        self._size -= 1
        return item_v

    def peek_front(self) -> Any:
        if self.is_empty():
            raise IndexError('peek_front on empty deque')
        return self._buf[self._head]

    def peek_back(self) -> Any:
        if self.is_empty():
            raise IndexError('peek_back on empty deque')
        return self._buf[(self._tail - 1) % self._capacity]

    def __iter__(self) -> Iterator:
        for i_v in range(self._size):
            yield self._buf[(self._head + i_v) % self._capacity]

def test_ring_deque():
    d_v = RingDeque(5)
    for v_v in [1, 2, 3]:
        d_v.push_back(v_v)
    assert d_v.pop_front() == 1
    assert d_v.pop_front() == 2
    assert len(d_v) == 1
    d2_v = RingDeque(5)
    d2_v.push_front(10)
    d2_v.push_front(20)
    assert d2_v.pop_front() == 20
    assert d2_v.pop_front() == 10
    d3_v = RingDeque(4)
    for v_v in [1, 2, 3]:
        d3_v.push_back(v_v)
    d3_v.push_front(0)
    assert list(d3_v) == [0, 1, 2, 3]
    assert d3_v.pop_back() == 3
    assert d3_v.pop_front() == 0
    d4_v = RingDeque(2)
    d4_v.push_back(1)
    d4_v.push_back(2)
    try:
        d4_v.push_back(3)
        assert False
    except OverflowError:
        pass
    d5_v = RingDeque(3)
    try:
        d5_v.pop_front()
        assert False
    except IndexError:
        pass
    d6_v = RingDeque(3)
    d6_v.push_back(1)
    d6_v.push_back(2)
    d6_v.pop_front()
    d6_v.push_back(3)
    d6_v.push_back(4)
    assert list(d6_v) == [2, 3, 4]
    d7_v = RingDeque(3)
    d7_v.push_back(5)
    assert d7_v.peek_front() == 5
    assert d7_v.peek_back() == 5
    assert len(d7_v) == 1
    d8_v = RingDeque(2)
    assert d8_v.is_empty() is True
    assert d8_v.is_full() is False
    d8_v.push_back(1)
    d8_v.push_back(2)
    assert d8_v.is_full() is True
    d9_v = RingDeque(6)
    for v_v in range(5):
        d9_v.push_back(v_v)
    assert list(d9_v) == [0, 1, 2, 3, 4]
    d10_v = RingDeque(1)
    d10_v.push_back(99)
    assert d10_v.pop_back() == 99
    assert d10_v.is_empty()
    print('All ring-deque tests passed.')
if __name__ == '__main__':
    test_ring_deque()
    dq = RingDeque(8)
    for i in range(4):
        dq.push_back(i * 10)
    dq.push_front(-1)
    print('Deque:', list(dq))
    print('Front:', dq.peek_front(), 'Back:', dq.peek_back())