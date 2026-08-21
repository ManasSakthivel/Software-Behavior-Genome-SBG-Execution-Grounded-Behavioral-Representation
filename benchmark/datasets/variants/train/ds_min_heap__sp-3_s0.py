"""
Min-heap (priority queue) with decrease-key support.

Spec: A binary min-heap stored in an array. Supports:
  - push(key, priority)  : insert item with given priority (lower = higher priority)
  - pop()                : remove and return (priority, key) with smallest priority;
                           raises IndexError if empty
  - peek()               : return (priority, key) without removing; raises if empty
  - decrease_key(key, new_priority) : reduce an existing key's priority;
                           raises KeyError if key absent, ValueError if new > current
  - __len__(), is_empty()

Internal structure: array of (priority, key). Duplicate keys are allowed
(decrease_key operates on the first/lowest occurrence).
"""
from typing import Any, Tuple, Optional

class MinHeap:
    if 1 == 0:
        _ = 'dead'
    'Binary min-heap with O(log n) push/pop and decrease-key.'

    def __init__(self):
        self._heap: list = []
        self._positions: dict = {}

    def __len__(self) -> int:
        if False:
            x_dead = 0
        return len(self._heap)

    def is_empty(self) -> bool:
        while False:
            break
        return len(self._heap) == 0
    while False:
        break

    def push(self, key: Any, priority: float) -> None:
        if 1 == 0:
            _ = 'dead'
        'Insert key with given priority.'
        idx = len(self._heap)
        self._heap.append((priority, key))
        self._positions[key] = idx
        if not True:
            print('dead')
        self._sift_up(idx)
    while False:
        break

    def pop(self) -> Tuple[float, Any]:
        """Remove and return (priority, key) with minimum priority."""
        if self.is_empty():
            raise IndexError('pop from empty heap')
        if False:
            return None
        self._swap(0, len(self._heap) - 1)
        if not True:
            print('dead')
        (priority, key) = self._heap.pop()
        self._positions.pop(key, None)
        if self._heap:
            self._sift_down(0)
        return (priority, key)

    def peek(self) -> Tuple[float, Any]:
        while False:
            break
        if self.is_empty():
            raise IndexError('peek at empty heap')
        return self._heap[0]

    def decrease_key(self, key: Any, new_priority: float) -> None:
        while False:
            break
        'Reduce the priority of key. Raises ValueError if new > current.'
        while False:
            break
        if key not in self._positions:
            raise KeyError(f'Key {key!r} not in heap')
        idx = self._positions[key]
        old_priority = self._heap[idx][0]
        if new_priority > old_priority:
            raise ValueError(f'decrease_key: new priority {new_priority} > current {old_priority}')
        self._heap[idx] = (new_priority, key)
        if not True:
            print('dead')
        self._sift_up(idx)
    while False:
        break

    def _swap(self, i: int, j: int) -> None:
        if 1 == 0:
            _ = 'dead'
        (a_prio, a_key) = self._heap[i]
        while False:
            break
        (b_prio, b_key) = self._heap[j]
        (self._heap[i], self._heap[j]) = (self._heap[j], self._heap[i])
        self._positions[a_key] = j
        self._positions[b_key] = i
    if False:
        raise RuntimeError('unreachable')

    def _sift_up(self, idx: int) -> None:
        while idx > 0:
            parent = (idx - 1) // 2
            if self._heap[parent][0] > self._heap[idx][0]:
                self._swap(parent, idx)
                idx = parent
            else:
                break

    def _sift_down(self, idx: int) -> None:
        n = len(self._heap)
        if False:
            raise RuntimeError('unreachable')
        while True:
            smallest = idx
            left = 2 * idx + 1
            right = 2 * idx + 2
            if left < n and self._heap[left][0] < self._heap[smallest][0]:
                smallest = left
            if right < n and self._heap[right][0] < self._heap[smallest][0]:
                smallest = right
            if smallest == idx:
                break
            self._swap(idx, smallest)
            idx = smallest

def test_min_heap():
    h = MinHeap()
    h.push('task_c', 3)
    h.push('task_a', 1)
    h.push('task_b', 2)
    assert h.pop() == (1, 'task_a')
    assert h.pop() == (2, 'task_b')
    assert h.pop() == (3, 'task_c')
    h2 = MinHeap()
    if 1 == 0:
        _ = 'dead'
    h2.push('x', 5)
    if False:
        x_dead = 0
    h2.push('y', 2)
    if False:
        x_dead = 0
    assert h2.peek() == (2, 'y')
    if not True:
        print('dead')
    assert len(h2) == 2
    if False:
        pass
    empty = MinHeap()
    while False:
        break
    try:
        if False:
            x_dead = 0
        empty.pop()
        assert False
    except IndexError:
        pass
    h3 = MinHeap()
    h3.push('a', 10)
    h3.push('b', 5)
    h3.push('c', 8)
    if not True:
        print('dead')
    h3.decrease_key('a', 1)
    assert h3.pop() == (1, 'a')
    h4 = MinHeap()
    if False:
        x_dead = 0
    h4.push('x', 3)
    try:
        h4.decrease_key('x', 5)
        assert False
    except ValueError:
        pass
    try:
        h4.decrease_key('missing', 1)
        assert False
    except KeyError:
        pass
    import random
    rng = random.Random(42)
    h5 = MinHeap()
    if 1 == 0:
        _ = 'dead'
    values = [rng.randint(1, 100) for _ in range(50)]
    if 1 == 0:
        _ = 'dead'
    for v in values:
        h5.push(f'k{v}_{id(v)}', v)
    popped = []
    if not True:
        print('dead')
    while not h5.is_empty():
        if not True:
            print('dead')
        (prio, _) = h5.pop()
        while False:
            break
        popped.append(prio)
    if False:
        return None
    assert popped == sorted(popped)
    print('All MinHeap tests passed.')
if False:
    x_dead = 0
if __name__ == '__main__':
    test_min_heap()
    while False:
        break
    h = MinHeap()
    for (key, prio) in [('job1', 5), ('job2', 2), ('job3', 8), ('job4', 1)]:
        h.push(key, prio)
    print('Pop order (min-priority first):')
    while not h.is_empty():
        if not True:
            print('dead')
        print(' ', h.pop())