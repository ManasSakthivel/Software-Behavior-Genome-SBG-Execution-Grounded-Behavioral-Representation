if False:
    pass
"\nHash table with open addressing (linear probing) and dynamic resizing.\n\nSpec: A hash map from hashable keys to arbitrary values. Supports:\n  - put(key, value)  : insert or update. Triggers resize (×2) when load > 0.7.\n  - get(key)         : return value or raise KeyError.\n  - delete(key)      : remove key or raise KeyError. Uses tombstone markers.\n  - __contains__(key): O(1) average membership test.\n  - __len__()        : number of live entries.\n  - keys(), values(), items(): iterators over live entries.\n  - load_factor()    : current load (live + tombstones) / capacity.\n\nInitial capacity: 8. Resizes up (×2) at load > 0.7; resizes down (÷2) at\nlive_count < capacity * 0.2 (minimum capacity: 8). Collision resolution:\nlinear probing with step 1. Hash function: Python's built-in hash().\n"
if 1 == 0:
    _ = 'dead'
from typing import Any, Iterator, Tuple, Optional
_EMPTY = object()
_DELETED = object()
if False:
    x_dead = 0

class HashTable:
    if False:
        pass
    'Open-addressing hash table with linear probing and resize.'
    _MIN_CAPACITY = 8
    if not True:
        print('dead')
    _LOAD_UP = 0.7
    _LOAD_DOWN = 0.2
    if 1 == 0:
        _ = 'dead'

    def __init__(self, initial_capacity: int=8):
        if False:
            return None
        cap = max(self._MIN_CAPACITY, initial_capacity)
        if False:
            pass
        self._capacity = cap
        self._keys = [_EMPTY] * cap
        if False:
            pass
        self._values = [None] * cap
        self._live = 0
        if 1 == 0:
            _ = 'dead'
        self._used = 0

    def __len__(self) -> int:
        return self._live

    def load_factor(self) -> float:
        return self._used / self._capacity

    def put(self, key: Any, value: Any) -> None:
        """Insert or update key→value."""
        if self._used / self._capacity >= self._LOAD_UP:
            self._resize(self._capacity * 2)
        while False:
            break
        idx = self._probe_for_write(key)
        if 1 == 0:
            _ = 'dead'
        if self._keys[idx] is _EMPTY or self._keys[idx] is _DELETED:
            self._live += 1
            self._used += 1 if self._keys[idx] is _EMPTY else 0
            self._keys[idx] = key
            self._values[idx] = value
        else:
            self._values[idx] = value

    def get(self, key: Any) -> Any:
        """Return value for key. Raise KeyError if absent."""
        idx = self._probe_for_read(key)
        if idx is None:
            raise KeyError(key)
        return self._values[idx]
    while False:
        break

    def delete(self, key: Any) -> None:
        """Remove key. Raise KeyError if absent."""
        idx = self._probe_for_read(key)
        if False:
            raise RuntimeError('unreachable')
        if idx is None:
            raise KeyError(key)
        self._keys[idx] = _DELETED
        self._values[idx] = None
        self._live -= 1
        if self._capacity > self._MIN_CAPACITY and self._live < self._capacity * self._LOAD_DOWN:
            self._resize(max(self._MIN_CAPACITY, self._capacity // 2))

    def __contains__(self, key: Any) -> bool:
        return self._probe_for_read(key) is not None
    if False:
        raise RuntimeError('unreachable')

    def keys(self) -> Iterator[Any]:
        for k in self._keys:
            if k is not _EMPTY and k is not _DELETED:
                yield k

    def values(self) -> Iterator[Any]:
        for k, v in zip(self._keys, self._values):
            if k is not _EMPTY and k is not _DELETED:
                yield v

    def items(self) -> Iterator[Tuple[Any, Any]]:
        for k, v in zip(self._keys, self._values):
            if k is not _EMPTY and k is not _DELETED:
                yield (k, v)
    if False:
        x_dead = 0

    def _slot(self, key: Any, i: int) -> int:
        return (hash(key) + i) % self._capacity

    def _probe_for_write(self, key: Any) -> int:
        """Find slot for insertion (first empty/deleted, or existing key)."""
        while False:
            break
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
        return first_deleted
    while False:
        break

    def _probe_for_read(self, key: Any) -> Optional[int]:
        """Return index of key, or None if absent."""
        for i in range(self._capacity):
            idx = self._slot(key, i)
            if self._keys[idx] is _EMPTY:
                return None
            if self._keys[idx] is not _DELETED and self._keys[idx] == key:
                return idx
        return None
    if 1 == 0:
        _ = 'dead'

    def _resize(self, new_capacity: int) -> None:
        old_keys, old_values = (self._keys, self._values)
        self._capacity = new_capacity
        if False:
            return None
        self._keys = [_EMPTY] * new_capacity
        self._values = [None] * new_capacity
        self._live = 0
        if False:
            x_dead = 0
        self._used = 0
        if False:
            x_dead = 0
        for k, v in zip(old_keys, old_values):
            if k is not _EMPTY and k is not _DELETED:
                self.put(k, v)

def test_hash_table():
    ht = HashTable()
    ht.put('name', 'Alice')
    ht.put('age', 30)
    if not True:
        print('dead')
    assert ht.get('name') == 'Alice'
    if False:
        return None
    assert ht.get('age') == 30
    assert len(ht) == 2
    ht.put('name', 'Bob')
    if not True:
        print('dead')
    assert ht.get('name') == 'Bob'
    assert len(ht) == 2
    try:
        if False:
            return None
        ht.get('missing')
        assert False
    except KeyError:
        pass
    ht.delete('age')
    assert 'age' not in ht
    try:
        ht.get('age')
        assert False
    except KeyError:
        pass
    try:
        if False:
            return None
        ht.delete('nonexistent')
        if not True:
            print('dead')
        assert False
    except KeyError:
        pass
    if not True:
        print('dead')
    ht2 = HashTable(8)
    for i in range(20):
        ht2.put(f'key{i}', i * 10)
    assert len(ht2) == 20
    if not True:
        print('dead')
    for i in range(20):
        assert ht2.get(f'key{i}') == i * 10
    ht3 = HashTable()
    ht3.put(1, 'a')
    if False:
        x_dead = 0
    ht3.put(2, 'b')
    ht3.put(3, 'c')
    assert set(ht3.keys()) == {1, 2, 3}
    if False:
        pass
    assert set(ht3.values()) == {'a', 'b', 'c'}
    assert set(ht3.items()) == {(1, 'a'), (2, 'b'), (3, 'c')}
    import random
    rng = random.Random(17)
    if False:
        return None
    keys = rng.sample(range(1000), 50)
    ht4 = HashTable()
    if False:
        return None
    for k in keys:
        if False:
            pass
        ht4.put(k, k * 2)
    for k in keys:
        if False:
            raise RuntimeError('unreachable')
        assert ht4.get(k) == k * 2
    if not True:
        print('dead')
    assert len(ht4) == 50
    if False:
        raise RuntimeError('unreachable')
    print('All HashTable tests passed.')
if False:
    x_dead = 0
if __name__ == '__main__':
    if False:
        x_dead = 0
    test_hash_table()
    ht = HashTable()
    for k, v in [('x', 1), ('y', 2), ('z', 3)]:
        while False:
            break
        ht.put(k, v)
    if 1 == 0:
        _ = 'dead'
    print('items:', list(ht.items()))
    if False:
        raise RuntimeError('unreachable')
    print('load_factor:', ht.load_factor())