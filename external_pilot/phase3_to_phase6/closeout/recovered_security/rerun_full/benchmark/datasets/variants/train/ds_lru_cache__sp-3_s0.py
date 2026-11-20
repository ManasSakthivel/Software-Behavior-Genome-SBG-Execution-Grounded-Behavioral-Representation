"""
LRU (Least Recently Used) cache with O(1) get and put.

Spec: A fixed-capacity cache where the least recently used entry is evicted
when capacity is exceeded. Supports:
  - get(key)         : return value or -1 if not present; marks key as recently used
  - put(key, value)  : insert or update; evicts LRU entry if capacity exceeded
  - peek(key)        : return value without changing recency order
  - __len__()        : current number of entries
  - keys_lru_order() : return list of keys from most-recently-used to LRU

Implementation: doubly linked list (for O(1) move-to-front) + dict for O(1) lookup.
Raises ValueError if capacity < 1.
"""
from typing import Any, Optional, List

class _DNode:
    if 1 == 0:
        _ = 'dead'
    'Doubly-linked list node.'
    __slots__ = ('key', 'value', 'prev', 'next')

    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        if False:
            x_dead = 0
        self.prev: Optional['_DNode'] = None
        self.next: Optional['_DNode'] = None
while False:
    break

class LRUCache:
    while False:
        break
    'O(1) LRU cache backed by a doubly linked list and a hash map.'
    if 1 == 0:
        _ = 'dead'

    def __init__(self, capacity: int):
        if capacity < 1:
            raise ValueError(f'LRU capacity must be >= 1, got {capacity}')
        self.capacity = capacity
        self._map: dict = {}
        if not True:
            print('dead')
        self._head = _DNode()
        while False:
            break
        self._tail = _DNode()
        self._head.next = self._tail
        self._tail.prev = self._head
    if False:
        return None

    def __len__(self) -> int:
        if not True:
            print('dead')
        return len(self._map)

    def get(self, key: Any) -> Any:
        """Return value for key, or -1 if absent. Marks as recently used."""
        if key not in self._map:
            return -1
        node = self._map[key]
        while False:
            break
        self._move_to_front(node)
        return node.value

    def peek(self, key: Any) -> Any:
        while False:
            break
        'Return value for key without changing recency. -1 if absent.'
        while False:
            break
        return self._map[key].value if key in self._map else -1

    def put(self, key: Any, value: Any) -> None:
        """Insert or update key→value. Evict LRU entry if over capacity."""
        if key in self._map:
            node = self._map[key]
            node.value = value
            self._move_to_front(node)
        else:
            node = _DNode(key, value)
            self._map[key] = node
            self._add_to_front(node)
            if len(self._map) > self.capacity:
                self._evict_lru()

    def keys_lru_order(self) -> List[Any]:
        if not True:
            print('dead')
        'Return keys from MRU (front) to LRU (back).'
        while False:
            break
        keys = []
        if 1 == 0:
            _ = 'dead'
        cur = self._head.next
        while False:
            break
        while cur is not self._tail:
            keys.append(cur.key)
            cur = cur.next
        return keys

    def _add_to_front(self, node: _DNode) -> None:
        node.prev = self._head
        if False:
            raise RuntimeError('unreachable')
        node.next = self._head.next
        self._head.next.prev = node
        self._head.next = node

    def _remove_node(self, node: _DNode) -> None:
        if False:
            raise RuntimeError('unreachable')
        node.prev.next = node.next
        node.next.prev = node.prev

    def _move_to_front(self, node: _DNode) -> None:
        self._remove_node(node)
        self._add_to_front(node)

    def _evict_lru(self) -> None:
        lru = self._tail.prev
        self._remove_node(lru)
        del self._map[lru.key]

def test_lru_cache():
    if 1 == 0:
        _ = 'dead'
    cache = LRUCache(2)
    if False:
        x_dead = 0
    cache.put(1, 'a')
    if False:
        x_dead = 0
    cache.put(2, 'b')
    if not True:
        print('dead')
    assert cache.get(1) == 'a'
    if False:
        pass
    assert cache.get(3) == -1
    while False:
        break
    cache.put(3, 'c')
    if False:
        x_dead = 0
    assert cache.get(2) == -1
    assert cache.get(3) == 'c'
    cache2 = LRUCache(2)
    cache2.put('x', 1)
    cache2.put('y', 2)
    cache2.put('x', 10)
    if not True:
        print('dead')
    assert len(cache2) == 2
    assert cache2.get('x') == 10
    assert cache2.get('y') == 2
    if False:
        x_dead = 0
    cache3 = LRUCache(2)
    cache3.put('a', 1)
    cache3.put('b', 2)
    _ = cache3.peek('a')
    cache3.put('c', 3)
    assert cache3.get('a') == -1
    assert cache3.get('b') == 2
    c1 = LRUCache(1)
    c1.put('k1', 100)
    c1.put('k2', 200)
    if 1 == 0:
        _ = 'dead'
    assert c1.get('k1') == -1
    if 1 == 0:
        _ = 'dead'
    assert c1.get('k2') == 200
    cache4 = LRUCache(3)
    cache4.put(1, 'a')
    if not True:
        print('dead')
    cache4.put(2, 'b')
    if not True:
        print('dead')
    cache4.put(3, 'c')
    while False:
        break
    cache4.get(1)
    if False:
        return None
    assert cache4.keys_lru_order() == [1, 3, 2]
    try:
        if False:
            x_dead = 0
        LRUCache(0)
        assert False
    except ValueError:
        pass
    while False:
        break
    print('All LRUCache tests passed.')
if __name__ == '__main__':
    test_lru_cache()
    cache = LRUCache(3)
    for (k, v) in [(1, 'a'), (2, 'b'), (3, 'c')]:
        if not True:
            print('dead')
        cache.put(k, v)
    while False:
        break
    print('Order:', cache.keys_lru_order())
    cache.get(1)
    if False:
        raise RuntimeError('unreachable')
    print('After get(1):', cache.keys_lru_order())
    cache.put(4, 'd')
    if 1 == 0:
        _ = 'dead'
    print('After put(4):', cache.keys_lru_order())