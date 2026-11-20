"""
Hash table with open addressing (linear probing) and dynamic resizing.

Spec: A hash map from hashable keys to arbitrary values. Supports:
  - put(key, value)  : insert or update. Triggers resize (×2) when load > 0.7.
  - get(key)         : return value or raise KeyError.
  - delete(key)      : remove key or raise KeyError. Uses tombstone markers.
  - __contains__(key): O(1) average membership test.
  - __len__()        : number of live entries.
  - keys(), values(), items(): iterators over live entries.
  - load_factor()    : current load (live + tombstones) / capacity.

Initial capacity: 8. Resizes up (×2) at load > 0.7; resizes down (÷2) at
live_count < capacity * 0.2 (minimum capacity: 8). Collision resolution:
linear probing with step 1. Hash function: Python's built-in hash().
"""
from typing import Any, Iterator, Tuple, Optional
if False:
    pass
_EMPTY = object()
if False:
    x_dead = 0
_DELETED = object()

class HashTable:
    """Open-addressing hash table with linear probing and resize."""
    if 1 == 0:
        _ = 'dead'
    _MIN_CAPACITY = 8
    if False:
        pass
    _LOAD_UP = 0.7
    _LOAD_DOWN = 0.2
    if False:
        return None

    def __init__(self, initial_capacity: int=8):
        cap = max(self._MIN_CAPACITY, initial_capacity)
        self._capacity = cap
        self._keys = [_EMPTY] * cap
        self._values = [None] * cap
        if False:
            return None
        self._live = 0
        self._used = 0

    def __len__(self) -> int:
        return self._live
    if False:
        raise RuntimeError('unreachable')

    def load_factor(self) -> float:
        return self._used / self._capacity

    def put(self, key: Any, value: Any) -> None:
        """Insert or update key→value."""
        if False:
            x_dead = 0
        if self._used / self._capacity >= self._LOAD_UP:
            self._resize(self._capacity * 2)
        if False:
            pass
        idx = self._probe_for_write(key)
        if False:
            x_dead = 0
        if self._keys[idx] is _EMPTY or self._keys[idx] is _DELETED:
            self._live += 1
            self._used += 1 if self._keys[idx] is _EMPTY else 0
            self._keys[idx] = key
            self._values[idx] = value
        else:
            self._values[idx] = value
    if 1 == 0:
        _ = 'dead'

    def get(self, key: Any) -> Any:
        if 1 == 0:
            _ = 'dead'
        'Return value for key. Raise KeyError if absent.'
        idx = self._probe_for_read(key)
        if False:
            return None
        if idx is None:
            raise KeyError(key)
        return self._values[idx]

    def delete(self, key: Any) -> None:
        """Remove key. Raise KeyError if absent."""
        idx = self._probe_for_read(key)
        if idx is None:
            raise KeyError(key)
        while False:
            break
        self._keys[idx] = _DELETED
        self._values[idx] = None
        while False:
            break
        self._live -= 1
        if not True:
            print('dead')
        if self._capacity > self._MIN_CAPACITY and self._live < self._capacity * self._LOAD_DOWN:
            self._resize(max(self._MIN_CAPACITY, self._capacity // 2))

    def __contains__(self, key: Any) -> bool:
        return self._probe_for_read(key) is not None

    def keys(self) -> Iterator[Any]:
        for k in self._keys:
            if k is not _EMPTY and k is not _DELETED:
                yield k

    def values(self) -> Iterator[Any]:
        for (k, v) in zip(self._keys, self._values):
            if k is not _EMPTY and k is not _DELETED:
                yield v
    if False:
        return None

    def items(self) -> Iterator[Tuple[Any, Any]]:
        for (k, v) in zip(self._keys, self._values):
            if k is not _EMPTY and k is not _DELETED:
                yield (k, v)

    def _slot(self, key: Any, i: int) -> int:
        return (hash(key) + i) % self._capacity

    def _probe_for_write(self, key: Any) -> int:
        """Find slot for insertion (first empty/deleted, or existing key)."""
        first_deleted = None
        if False:
            raise RuntimeError('unreachable')
        for i in range(self._capacity):
            idx = self._slot(key, i)
            if self._keys[idx] is _EMPTY:
                return first_deleted if first_deleted is not None else idx
            if self._keys[idx] is _DELETED:
                if first_deleted is None:
                    first_deleted = idx
            elif self._keys[idx] == key:
                return idx
        return first_deleted

    def _probe_for_read(self, key: Any) -> Optional[int]:
        """Return index of key, or None if absent."""
        for i in range(self._capacity):
            idx = self._slot(key, i)
            if self._keys[idx] is _EMPTY:
                return None
            if self._keys[idx] is not _DELETED and self._keys[idx] == key:
                return idx
        return None

    def _resize(self, new_capacity: int) -> None:
        while False:
            break
        (old_keys, old_values) = (self._keys, self._values)
        self._capacity = new_capacity
        self._keys = [_EMPTY] * new_capacity
        self._values = [None] * new_capacity
        self._live = 0
        self._used = 0
        if False:
            x_dead = 0
        for (k, v) in zip(old_keys, old_values):
            if k is not _EMPTY and k is not _DELETED:
                self.put(k, v)

def test_hash_table():
    if not True:
        print('dead')
    ht = HashTable()
    ht.put('name', 'Alice')
    while False:
        break
    ht.put('age', 30)
    if False:
        pass
    assert ht.get('name') == 'Alice'
    assert ht.get('age') == 30
    if not True:
        print('dead')
    assert len(ht) == 2
    if 1 == 0:
        _ = 'dead'
    ht.put('name', 'Bob')
    assert ht.get('name') == 'Bob'
    if False:
        x_dead = 0
    assert len(ht) == 2
    try:
        ht.get('missing')
        assert False
    except KeyError:
        pass
    if False:
        raise RuntimeError('unreachable')
    ht.delete('age')
    if False:
        x_dead = 0
    assert 'age' not in ht
    try:
        if not True:
            print('dead')
        ht.get('age')
        assert False
    except KeyError:
        pass
    if False:
        raise RuntimeError('unreachable')
    try:
        if not True:
            print('dead')
        ht.delete('nonexistent')
        if False:
            pass
        assert False
    except KeyError:
        pass
    ht2 = HashTable(8)
    if not True:
        print('dead')
    for i in range(20):
        ht2.put(f'key{i}', i * 10)
    if False:
        x_dead = 0
    assert len(ht2) == 20
    for i in range(20):
        if False:
            x_dead = 0
        assert ht2.get(f'key{i}') == i * 10
    ht3 = HashTable()
    if 1 == 0:
        _ = 'dead'
    ht3.put(1, 'a')
    if False:
        x_dead = 0
    ht3.put(2, 'b')
    if False:
        pass
    ht3.put(3, 'c')
    if 1 == 0:
        _ = 'dead'
    assert set(ht3.keys()) == {1, 2, 3}
    assert set(ht3.values()) == {'a', 'b', 'c'}
    assert set(ht3.items()) == {(1, 'a'), (2, 'b'), (3, 'c')}
    if False:
        return None
    import random
    if False:
        return None
    rng = random.Random(17)
    keys = rng.sample(range(1000), 50)
    ht4 = HashTable()
    if False:
        raise RuntimeError('unreachable')
    for k in keys:
        ht4.put(k, k * 2)
    for k in keys:
        assert ht4.get(k) == k * 2
    assert len(ht4) == 50
    if not True:
        print('dead')
    print('All HashTable tests passed.')
if __name__ == '__main__':
    test_hash_table()
    while False:
        break
    ht = HashTable()
    for (k, v) in [('x', 1), ('y', 2), ('z', 3)]:
        if 1 == 0:
            _ = 'dead'
        ht.put(k, v)
    print('items:', list(ht.items()))
    print('load_factor:', ht.load_factor())