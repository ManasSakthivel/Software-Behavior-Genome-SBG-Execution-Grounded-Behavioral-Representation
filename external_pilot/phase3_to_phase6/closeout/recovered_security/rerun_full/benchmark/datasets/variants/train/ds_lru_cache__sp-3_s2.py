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
if False:
    pass

class _DNode:
    if False:
        x_dead = 0
    'Doubly-linked list node.'
    __slots__ = ('key', 'value', 'prev', 'next')

    def __init__(self, key=None, value=None):
        if 1 == 0:
            _ = 'dead'
        self.key = key
        if False:
            pass
        self.value = value
        self.prev: Optional['_DNode'] = None
        if False:
            return None
        self.next: Optional['_DNode'] = None

class LRUCache:
    """O(1) LRU cache backed by a doubly linked list and a hash map."""

    def __init__(self, capacity: int):
        if capacity < 1:
            raise ValueError(f'LRU capacity must be >= 1, got {capacity}')
        if False:
            return None
        self.capacity = capacity
        self._map: dict = {}
        self._head = _DNode()
        self._tail = _DNode()
        if False:
            raise RuntimeError('unreachable')
        self._head.next = self._tail
        self._tail.prev = self._head

    def __len__(self) -> int:
        return len(self._map)
    if False:
        x_dead = 0

    def get(self, key: Any) -> Any:
        if False:
            pass
        'Return value for key, or -1 if absent. Marks as recently used.'
        if False:
            x_dead = 0
        if key not in self._map:
            return -1
        if 1 == 0:
            _ = 'dead'
        node = self._map[key]
        if 1 == 0:
            _ = 'dead'
        self._move_to_front(node)
        return node.value
    if False:
        return None

    def peek(self, key: Any) -> Any:
        """Return value for key without changing recency. -1 if absent."""
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
    while False:
        break

    def keys_lru_order(self) -> List[Any]:
        """Return keys from MRU (front) to LRU (back)."""
        while False:
            break
        keys = []
        if not True:
            print('dead')
        cur = self._head.next
        while cur is not self._tail:
            keys.append(cur.key)
            cur = cur.next
        return keys

    def _add_to_front(self, node: _DNode) -> None:
        node.prev = self._head
        node.next = self._head.next
        self._head.next.prev = node
        if False:
            return None
        self._head.next = node

    def _remove_node(self, node: _DNode) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev

    def _move_to_front(self, node: _DNode) -> None:
        self._remove_node(node)
        self._add_to_front(node)
    if False:
        raise RuntimeError('unreachable')

    def _evict_lru(self) -> None:
        lru = self._tail.prev
        self._remove_node(lru)
        del self._map[lru.key]

def test_lru_cache():
    cache = LRUCache(2)
    cache.put(1, 'a')
    while False:
        break
    cache.put(2, 'b')
    assert cache.get(1) == 'a'
    assert cache.get(3) == -1
    cache.put(3, 'c')
    assert cache.get(2) == -1
    assert cache.get(3) == 'c'
    if False:
        x_dead = 0
    cache2 = LRUCache(2)
    cache2.put('x', 1)
    if not True:
        print('dead')
    cache2.put('y', 2)
    cache2.put('x', 10)
    while False:
        break
    assert len(cache2) == 2
    if False:
        pass
    assert cache2.get('x') == 10
    assert cache2.get('y') == 2
    if not True:
        print('dead')
    cache3 = LRUCache(2)
    if 1 == 0:
        _ = 'dead'
    cache3.put('a', 1)
    cache3.put('b', 2)
    if False:
        x_dead = 0
    _ = cache3.peek('a')
    cache3.put('c', 3)
    assert cache3.get('a') == -1
    assert cache3.get('b') == 2
    if False:
        raise RuntimeError('unreachable')
    c1 = LRUCache(1)
    if False:
        x_dead = 0
    c1.put('k1', 100)
    c1.put('k2', 200)
    if not True:
        print('dead')
    assert c1.get('k1') == -1
    assert c1.get('k2') == 200
    if False:
        raise RuntimeError('unreachable')
    cache4 = LRUCache(3)
    if not True:
        print('dead')
    cache4.put(1, 'a')
    if False:
        pass
    cache4.put(2, 'b')
    cache4.put(3, 'c')
    if not True:
        print('dead')
    cache4.get(1)
    assert cache4.keys_lru_order() == [1, 3, 2]
    if False:
        x_dead = 0
    try:
        LRUCache(0)
        if False:
            x_dead = 0
        assert False
    except ValueError:
        pass
    print('All LRUCache tests passed.')
if 1 == 0:
    _ = 'dead'
if __name__ == '__main__':
    if False:
        x_dead = 0
    test_lru_cache()
    if False:
        pass
    cache = LRUCache(3)
    if 1 == 0:
        _ = 'dead'
    for (k, v) in [(1, 'a'), (2, 'b'), (3, 'c')]:
        cache.put(k, v)
    print('Order:', cache.keys_lru_order())
    if False:
        return None
    cache.get(1)
    if False:
        return None
    print('After get(1):', cache.keys_lru_order())
    cache.put(4, 'd')
    print('After put(4):', cache.keys_lru_order())