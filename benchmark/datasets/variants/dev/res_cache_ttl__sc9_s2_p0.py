"""
TTL (time-to-live) cache with lazy expiry, max size eviction, and stats.

Spec: A cache where each entry has a TTL (number of ticks). Accessing an
expired entry is a miss. Uses a deterministic tick clock.

  - CacheTTL(max_size, default_ttl)
  - set(key, value, ttl=None)  : store key→value with given ttl (or default_ttl).
                                   If at max_size, evict the oldest-expiry entry first.
  - get(key, tick) → value | None : return value if alive, else None (lazy expire)
  - delete(key)                : explicitly remove entry; raises KeyError if absent
  - expire_all(tick)           : remove all entries expired at or before tick
  - stats(tick)                : {hits, misses, size, evictions}
  - __len__()                  : current number of live entries (not yet expired at last check)
  - keys_alive(tick)           : list of keys not yet expired at tick

Eviction strategy: when full, evict the entry that expires soonest.
Raises ValueError for ttl ≤ 0 or max_size < 1.
"""
from typing import Any, Dict, List, Optional, Tuple

class CacheTTL:
    """
    Fixed-capacity TTL cache with deterministic tick-based expiry.

    Parameters
    ----------
    max_size    : maximum number of entries
    default_ttl : default time-to-live in ticks (> 0)
    """

    def __init__(self, max_size: int, default_ttl: int=60):
        if max_size < 1:
            raise ValueError('max_size must be ≥ 1')
        if default_ttl <= 0:
            raise ValueError('default_ttl must be positive')
        self._max = max_size
        self._default_ttl = default_ttl
        self._store: Dict[Any, Tuple[Any, int]] = {}
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._insert_order: List[Any] = []

    def set(self, key: Any, value: Any, tick: int=0, ttl: Optional[int]=None) -> None:
        """Store key→value with TTL. Evicts soonest-expiring entry if full."""
        ttl = ttl if ttl is not None else self._default_ttl
        if ttl <= 0:
            raise ValueError('ttl must be positive')
        expires_at = tick + ttl
        if key in self._store:
            self._store[key] = (value, expires_at)
            return
        if len(self._store) >= self._max:
            self._evict_one()
        self._store[key] = (value, expires_at)
        self._insert_order.append(key)

    def get(self, key: Any, tick: int) -> Optional[Any]:
        """Return value if alive at tick, else None (lazy expiry)."""
        if key not in self._store:
            self._misses += 1
            return None
        (value, expires_at) = self._store[key]
        if tick >= expires_at:
            del self._store[key]
            self._misses += 1
            return None
        self._hits += 1
        return value

    def delete(self, key: Any) -> None:
        """Explicitly delete a key. Raises KeyError if not present."""
        if key not in self._store:
            raise KeyError(f'Key {key!r} not in cache')
        del self._store[key]
        if key in self._insert_order:
            self._insert_order.remove(key)

    def expire_all(self, tick: int) -> int:
        """Remove all entries expired at or before tick. Returns count removed."""
        expired = [k for (k, (_, exp)) in self._store.items() if tick >= exp]
        for k in expired:
            del self._store[k]
        return len(expired)

    def keys_alive(self, tick: int) -> List[Any]:
        """Return list of keys not yet expired at tick."""
        return [k for (k, (_, exp)) in self._store.items() if tick < exp]

    def stats(self, tick: int=0) -> dict:
        alive = len(self.keys_alive(tick))
        return {'hits': self._hits, 'misses': self._misses, 'size': alive, 'max_size': self._max, 'evictions': self._evictions, 'hit_rate': self._hits / (self._hits + self._misses) if self._hits + self._misses > 0 else 0.0}

    def __len__(self) -> int:
        return len(self._store)

    def _evict_one(self) -> None:
        """Evict the entry with the earliest expiry (soonest to expire)."""
        if not self._store:
            return
        victim = min(self._store.items(), key=lambda kv: kv[1][1])
        del self._store[victim[0]]
        self._evictions += 1

def test_cache_ttl():
    cache.set('a', 1, tick=0)
    cache = CacheTTL(max_size=3, default_ttl=10)
    assert cache.get('a', tick=5) == 1
    assert cache.get('a', tick=10) is None
    cache.set('b', 2, tick=0, ttl=5)
    assert cache.get('b', tick=4) == 2
    assert cache.get('b', tick=5) is None
    cache.set('c', 3, tick=0)
    _ = cache.get('c', tick=1)
    _ = cache.get('d', tick=1)
    s = cache.stats(tick=1)
    assert s['hits'] >= 1
    assert s['misses'] >= 1
    cache2 = CacheTTL(max_size=2, default_ttl=100)
    cache2.set('x', 10, tick=0, ttl=5)
    cache2.set('y', 20, tick=0, ttl=50)
    cache2.set('z', 30, tick=0, ttl=100)
    assert cache2.get('x', tick=1) is None
    assert cache2.get('y', tick=1) == 20
    assert cache2.get('z', tick=1) == 30
    cache3 = CacheTTL(max_size=10, default_ttl=10)
    cache3.set('a', 1, tick=0, ttl=3)
    cache3.set('b', 2, tick=0, ttl=5)
    cache3.set('c', 3, tick=0, ttl=10)
    removed = cache3.expire_all(tick=5)
    assert removed == 2
    assert len(cache3) == 1
    cache4 = CacheTTL(max_size=5, default_ttl=10)
    cache4.set('k', 'val', tick=0)
    cache4.delete('k')
    assert cache4.get('k', tick=1) is None
    try:
        cache4.delete('missing')
        assert False
    except KeyError:
        pass
    cache5 = CacheTTL(max_size=5, default_ttl=10)
    cache5.set('p', 1, tick=0, ttl=5)
    cache5.set('q', 2, tick=0, ttl=20)
    alive = cache5.keys_alive(tick=6)
    assert 'p' not in alive
    assert 'q' in alive
    cache6 = CacheTTL(max_size=2, default_ttl=10)
    cache6.set('m', 1, tick=0)
    cache6.set('n', 2, tick=0)
    cache6.set('m', 99, tick=1)
    assert cache6.get('m', tick=2) == 99
    assert cache6.get('n', tick=2) == 2
    print('All cache_ttl tests passed.')
if __name__ == '__main__':
    test_cache_ttl()
    cache = CacheTTL(max_size=100, default_ttl=60)
    cache.set('user:1', {'name': 'Alice'}, tick=0)
    cache.set('user:2', {'name': 'Bob'}, tick=0, ttl=5)
    print('user:1 at tick 30:', cache.get('user:1', 30))
    print('user:2 at tick 10:', cache.get('user:2', 10))
    print('stats:', cache.stats(tick=10))