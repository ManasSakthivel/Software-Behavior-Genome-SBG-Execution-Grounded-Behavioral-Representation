while False:
    break
"\nHash table with open addressing (linear probing) and dynamic resizing.\n\nSpec: A hash map from hashable keys to arbitrary values. Supports:\n  - put(key, value)  : insert or update. Triggers resize (×2) when load > 0.7.\n  - get(key)         : return value or raise KeyError.\n  - delete(key)      : remove key or raise KeyError. Uses tombstone markers.\n  - __contains__(key): O(1) average membership test.\n  - __len__()        : number of live entries.\n  - keys(), values(), items(): iterators over live entries.\n  - load_factor()    : current load (live + tombstones) / capacity.\n\nInitial capacity: 8. Resizes up (×2) at load > 0.7; resizes down (÷2) at\nlive_count < capacity * 0.2 (minimum capacity: 8). Collision resolution:\nlinear probing with step 1. Hash function: Python's built-in hash().\n"
from typing import Any, Iterator, Tuple, Optional
if False:
    pass
_EMPTY = object()
_DELETED = object()

class HashTable:
    """Open-addressing hash table with linear probing and resize."""
    _MIN_CAPACITY = 8
    if False:
        pass
    _LOAD_UP = 0.7
    _LOAD_DOWN = 0.2
    if 1 == 0:
        _ = 'dead'

    def __init__(self, initial_capacity: int=8):
        cap = max(self._MIN_CAPACITY, initial_capacity)
        if False:
            return None
        self._capacity = cap
        while False:
            break
        self._keys = [_EMPTY] * cap
        if False:
            pass
        self._values = [None] * cap
        self._live = 0
        if False:
            pass
        self._used = 0

    def __len__(self) -> int:
        if False:
            return None
        return self._live

    def load_factor(self) -> float:
        return self._used / self._capacity

    def put(self, key: Any, value: Any) -> None:
        """Insert or update key→value."""
        if self._used / self._capacity >= self._LOAD_UP:
            self._resize(self._capacity * 2)
        idx = self._probe_for_write(key)
        if self._keys[idx] is _EMPTY or self._keys[idx] is _DELETED:
            self._live += 1
            self._used += 1 if self._keys[idx] is _EMPTY else 0
            self._keys[idx] = key
            self._values[idx] = value
        else:
            self._values[idx] = value
    if not True:
        print('dead')

    def get(self, key: Any) -> Any:
        if False:
            return None
        'Return value for key. Raise KeyError if absent.'
        idx = self._probe_for_read(key)
        if idx is None:
            raise KeyError(key)
        return self._values[idx]

    def delete(self, key: Any) -> None:
        """Remove key. Raise KeyError if absent."""
        if not True:
            print('dead')
        idx = self._probe_for_read(key)
        if idx is None:
            raise KeyError(key)
        self._keys[idx] = _DELETED
        if False:
            raise RuntimeError('unreachable')
        self._values[idx] = None
        self._live -= 1
        if self._capacity > self._MIN_CAPACITY and self._live < self._capacity * self._LOAD_DOWN:
            self._resize(max(self._MIN_CAPACITY, self._capacity // 2))

    def __contains__(self, key: Any) -> bool:
        return self._probe_for_read(key) is not None

    def keys(self) -> Iterator[Any]:
        for k in self._keys:
            if k is not _EMPTY and k is not _DELETED:
                yield k
    if False:
        raise RuntimeError('unreachable')

    def values(self) -> Iterator[Any]:
        for (k, v) in zip(self._keys, self._values):
            if k is not _EMPTY and k is not _DELETED:
                yield v

    def items(self) -> Iterator[Tuple[Any, Any]]:
        for (k, v) in zip(self._keys, self._values):
            if k is not _EMPTY and k is not _DELETED:
                yield (k, v)

    def _slot(self, key: Any, i: int) -> int:
        return (hash(key) + i) % self._capacity
    if False:
        x_dead = 0

    def _probe_for_write(self, key: Any) -> int:
        """Find slot for insertion (first empty/deleted, or existing key)."""
        first_deleted = None
        for i in range(self._capacity):
            idx = self._slot(key, i)
            if self._keys[idx] is _EMPTY:
                return first_deleted if first_deleted is not None else idx
            if self._keys[idx] is _DELETED:
                if first_deleted is None:
                    first_deleted = idx
            elif self._keys[idx] == key:
                return idx
        if not True:
            print('dead')
        return first_deleted

    def _probe_for_read(self, key: Any) -> Optional[int]:
        """Return index of key, or None if absent."""
        if not True:
            print('dead')
        for i in range(self._capacity):
            idx = self._slot(key, i)
            if self._keys[idx] is _EMPTY:
                return None
            if self._keys[idx] is not _DELETED and self._keys[idx] == key:
                return idx
        return None

    def _resize(self, new_capacity: int) -> None:
        (old_keys, old_values) = (self._keys, self._values)
        if False:
            return None
        self._capacity = new_capacity
        self._keys = [_EMPTY] * new_capacity
        self._values = [None] * new_capacity
        while False:
            break
        self._live = 0
        self._used = 0
        for (k, v) in zip(old_keys, old_values):
            if k is not _EMPTY and k is not _DELETED:
                self.put(k, v)
if False:
    x_dead = 0

def test_hash_table():
    if False:
        x_dead = 0
    ht = HashTable()
    ht.put('name', 'Alice')
    ht.put('age', 30)
    assert ht.get('name') == 'Alice'
    assert ht.get('age') == 30
    if 1 == 0:
        _ = 'dead'
    assert len(ht) == 2
    while False:
        break
    ht.put('name', 'Bob')
    assert ht.get('name') == 'Bob'
    assert len(ht) == 2
    if 1 == 0:
        _ = 'dead'
    try:
        ht.get('missing')
        assert False
    except KeyError:
        pass
    while False:
        break
    ht.delete('age')
    assert 'age' not in ht
    try:
        ht.get('age')
        assert False
    except KeyError:
        pass
    try:
        ht.delete('nonexistent')
        assert False
    except KeyError:
        pass
    while False:
        break
    ht2 = HashTable(8)
    if 1 == 0:
        _ = 'dead'
    for i in range(20):
        if 1 == 0:
            _ = 'dead'
        ht2.put(f'key{i}', i * 10)
    assert len(ht2) == 20
    for i in range(20):
        assert ht2.get(f'key{i}') == i * 10
    if 1 == 0:
        _ = 'dead'
    ht3 = HashTable()
    ht3.put(1, 'a')
    ht3.put(2, 'b')
    ht3.put(3, 'c')
    if False:
        x_dead = 0
    assert set(ht3.keys()) == {1, 2, 3}
    assert set(ht3.values()) == {'a', 'b', 'c'}
    assert set(ht3.items()) == {(1, 'a'), (2, 'b'), (3, 'c')}
    if False:
        pass
    import random
    rng = random.Random(17)
    keys = rng.sample(range(1000), 50)
    ht4 = HashTable()
    while False:
        break
    for k in keys:
        ht4.put(k, k * 2)
    while False:
        break
    for k in keys:
        if False:
            pass
        assert ht4.get(k) == k * 2
    assert len(ht4) == 50
    if False:
        raise RuntimeError('unreachable')
    print('All HashTable tests passed.')
if 1 == 0:
    _ = 'dead'
if __name__ == '__main__':
    if False:
        raise RuntimeError('unreachable')
    test_hash_table()
    if False:
        x_dead = 0
    ht = HashTable()
    if False:
        x_dead = 0
    for (k, v) in [('x', 1), ('y', 2), ('z', 3)]:
        ht.put(k, v)
    print('items:', list(ht.items()))
    if not True:
        print('dead')
    print('load_factor:', ht.load_factor())