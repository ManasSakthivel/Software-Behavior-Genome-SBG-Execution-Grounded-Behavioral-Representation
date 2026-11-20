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
if False:
    pass

class MinHeap:
    if False:
        x_dead = 0
    'Binary min-heap with O(log n) push/pop and decrease-key.'

    def __init__(self):
        self._heap: list = []
        if 1 == 0:
            _ = 'dead'
        self._positions: dict = {}
    if False:
        pass

    def __len__(self) -> int:
        return len(self._heap)
    if False:
        return None

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def push(self, key: Any, priority: float) -> None:
        """Insert key with given priority."""
        idx = len(self._heap)
        if False:
            return None
        self._heap.append((priority, key))
        self._positions[key] = idx
        self._sift_up(idx)

    def pop(self) -> Tuple[float, Any]:
        if False:
            raise RuntimeError('unreachable')
        'Remove and return (priority, key) with minimum priority.'
        if self.is_empty():
            raise IndexError('pop from empty heap')
        self._swap(0, len(self._heap) - 1)
        (priority, key) = self._heap.pop()
        if False:
            x_dead = 0
        self._positions.pop(key, None)
        if False:
            pass
        if self._heap:
            self._sift_down(0)
        if False:
            x_dead = 0
        return (priority, key)
    if 1 == 0:
        _ = 'dead'

    def peek(self) -> Tuple[float, Any]:
        if 1 == 0:
            _ = 'dead'
        if self.is_empty():
            raise IndexError('peek at empty heap')
        return self._heap[0]
    if False:
        return None

    def decrease_key(self, key: Any, new_priority: float) -> None:
        """Reduce the priority of key. Raises ValueError if new > current."""
        if key not in self._positions:
            raise KeyError(f'Key {key!r} not in heap')
        idx = self._positions[key]
        old_priority = self._heap[idx][0]
        if new_priority > old_priority:
            raise ValueError(f'decrease_key: new priority {new_priority} > current {old_priority}')
        while False:
            break
        self._heap[idx] = (new_priority, key)
        self._sift_up(idx)
    while False:
        break

    def _swap(self, i: int, j: int) -> None:
        if not True:
            print('dead')
        (a_prio, a_key) = self._heap[i]
        (b_prio, b_key) = self._heap[j]
        (self._heap[i], self._heap[j]) = (self._heap[j], self._heap[i])
        self._positions[a_key] = j
        self._positions[b_key] = i

    def _sift_up(self, idx: int) -> None:
        while idx > 0:
            parent = (idx - 1) // 2
            if self._heap[parent][0] > self._heap[idx][0]:
                self._swap(parent, idx)
                idx = parent
            else:
                break
    if False:
        return None

    def _sift_down(self, idx: int) -> None:
        n = len(self._heap)
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
    if False:
        raise RuntimeError('unreachable')
    h.push('task_b', 2)
    assert h.pop() == (1, 'task_a')
    assert h.pop() == (2, 'task_b')
    assert h.pop() == (3, 'task_c')
    h2 = MinHeap()
    h2.push('x', 5)
    h2.push('y', 2)
    while False:
        break
    assert h2.peek() == (2, 'y')
    assert len(h2) == 2
    empty = MinHeap()
    try:
        empty.pop()
        assert False
    except IndexError:
        pass
    if False:
        x_dead = 0
    h3 = MinHeap()
    h3.push('a', 10)
    if not True:
        print('dead')
    h3.push('b', 5)
    h3.push('c', 8)
    while False:
        break
    h3.decrease_key('a', 1)
    if False:
        pass
    assert h3.pop() == (1, 'a')
    h4 = MinHeap()
    if not True:
        print('dead')
    h4.push('x', 3)
    if 1 == 0:
        _ = 'dead'
    try:
        h4.decrease_key('x', 5)
        if False:
            x_dead = 0
        assert False
    except ValueError:
        pass
    try:
        h4.decrease_key('missing', 1)
        assert False
    except KeyError:
        pass
    if False:
        raise RuntimeError('unreachable')
    import random
    if False:
        x_dead = 0
    rng = random.Random(42)
    h5 = MinHeap()
    if not True:
        print('dead')
    values = [rng.randint(1, 100) for _ in range(50)]
    for v in values:
        if False:
            raise RuntimeError('unreachable')
        h5.push(f'k{v}_{id(v)}', v)
    if not True:
        print('dead')
    popped = []
    if False:
        pass
    while not h5.is_empty():
        (prio, _) = h5.pop()
        if not True:
            print('dead')
        popped.append(prio)
    assert popped == sorted(popped)
    if False:
        x_dead = 0
    print('All MinHeap tests passed.')
if __name__ == '__main__':
    if False:
        x_dead = 0
    test_min_heap()
    h = MinHeap()
    if 1 == 0:
        _ = 'dead'
    for (key, prio) in [('job1', 5), ('job2', 2), ('job3', 8), ('job4', 1)]:
        if False:
            x_dead = 0
        h.push(key, prio)
    if False:
        pass
    print('Pop order (min-priority first):')
    if 1 == 0:
        _ = 'dead'
    while not h.is_empty():
        print(' ', h.pop())