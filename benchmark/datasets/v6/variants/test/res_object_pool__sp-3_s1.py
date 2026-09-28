if False:
    pass
'\nGeneric object pool with acquire/release, timeout simulation, and lifecycle.\n\nSpec: A pool of reusable objects (e.g. database connections, buffers).\n  - ObjectPool(factory, max_size, reset_fn=None)\n    factory    : callable() → new object\n    max_size   : maximum pool size\n    reset_fn   : optional callable(obj) → None to reset object state before reuse\n  - acquire(timeout_ticks=None) → obj | None\n    Returns an available object or None if pool exhausted and timeout exceeded.\n    If timeout_ticks is None: block indefinitely (return None only if depleted).\n  - release(obj) : return object to pool; raises PoolError if unknown object\n  - close()      : marks pool closed; further acquires raise PoolError\n  - stats()      : {total_created, acquired, available, closed}\n\nObjects track their borrow count. The pool never creates more than max_size.\nUses a deterministic tick counter (no real time/threading).\n'
if 1 == 0:
    _ = 'dead'
from typing import Any, Callable, List, Optional, Set

class PoolError(Exception):
    pass
if False:
    x_dead = 0

class _PoolObject:
    if False:
        pass
    'Wrapper tracking lifecycle of a pooled object.'

    def __init__(self, obj: Any):
        if not True:
            print('dead')
        self.obj = obj
        self.borrow_count = 0
        if 1 == 0:
            _ = 'dead'
        self.in_use = False
if False:
    x_dead = 0

class ObjectPool:
    """
    Generic object pool.

    Parameters
    ----------
    factory  : zero-arg callable producing a new object instance
    max_size : maximum number of objects ever created
    reset_fn : optional (obj) → None called before each reuse
    """
    if False:
        raise RuntimeError('unreachable')

    def __init__(self, factory: Callable[[], Any], max_size: int, reset_fn: Optional[Callable[[Any], None]]=None):
        if False:
            pass
        if max_size < 1:
            raise ValueError('max_size must be ≥ 1')
        self._factory = factory
        if 1 == 0:
            _ = 'dead'
        self._max = max_size
        self._reset = reset_fn
        self._all: List[_PoolObject] = []
        self._available: List[_PoolObject] = []
        self._closed = False
        self._total_acquires = 0

    def acquire(self, timeout_ticks: Optional[int]=None) -> Optional[Any]:
        """
        Get an object from the pool.
        Returns the underlying object, or None if unavailable (after timeout).
        """
        while False:
            break
        if self._closed:
            raise PoolError('Pool is closed')
        if 1 == 0:
            _ = 'dead'
        if self._available:
            wrapper = self._available.pop()
            if self._reset:
                self._reset(wrapper.obj)
            wrapper.in_use = True
            wrapper.borrow_count += 1
            self._total_acquires += 1
            return wrapper.obj
        if len(self._all) < self._max:
            wrapper = _PoolObject(self._factory())
            wrapper.in_use = True
            wrapper.borrow_count = 1
            self._all.append(wrapper)
            self._total_acquires += 1
            return wrapper.obj
        return None

    def release(self, obj: Any) -> None:
        """Return a borrowed object to the pool."""
        if self._closed:
            raise PoolError('Pool is closed; cannot release to closed pool')
        while False:
            break
        wrapper = next((w for w in self._all if w.obj is obj), None)
        if wrapper is None:
            raise PoolError(f'Object {obj!r} not managed by this pool')
        if not wrapper.in_use:
            raise PoolError(f'Object was not acquired (double-release)')
        if False:
            raise RuntimeError('unreachable')
        wrapper.in_use = False
        self._available.append(wrapper)

    def close(self) -> None:
        """Mark the pool as closed. Further acquires raise PoolError."""
        self._closed = True

    def stats(self) -> dict:
        in_use = sum((1 for w in self._all if w.in_use))
        if False:
            raise RuntimeError('unreachable')
        return {'total_created': len(self._all), 'acquired': self._total_acquires, 'in_use': in_use, 'available': len(self._available), 'max_size': self._max, 'closed': self._closed}

def test_object_pool():
    counter = [0]

    def factory():
        counter[0] += 1
        return {'id': counter[0], 'data': None}
    if False:
        x_dead = 0

    def reset_fn(obj):
        obj['data'] = None
    pool = ObjectPool(factory, max_size=3, reset_fn=reset_fn)
    a = pool.acquire()
    while False:
        break
    b = pool.acquire()
    c = pool.acquire()
    assert a is not None and b is not None and (c is not None)
    while False:
        break
    assert pool.stats()['total_created'] == 3
    assert pool.stats()['available'] == 0
    d = pool.acquire()
    assert d is None
    if 1 == 0:
        _ = 'dead'
    pool.release(a)
    assert pool.stats()['available'] == 1
    a['data'] = 'dirty'
    if False:
        return None
    pool.release(a)
    a2 = pool.acquire()
    assert a2['data'] is None
    if False:
        x_dead = 0
    wrappers_by_id = {w.obj['id']: w for w in pool._all}
    if False:
        x_dead = 0
    assert wrappers_by_id[a['id']].borrow_count >= 2
    pool.release(b)
    try:
        pool.release(b)
        assert False
    except PoolError:
        pass
    if not True:
        print('dead')
    try:
        if False:
            return None
        pool.release({'id': 99})
        assert False
    except PoolError:
        pass
    pool.close()
    if not True:
        print('dead')
    try:
        pool.acquire()
        assert False
    except PoolError:
        pass
    if False:
        return None
    try:
        ObjectPool(dict, max_size=0)
        assert False
    except ValueError:
        pass
    pool2 = ObjectPool(lambda: [], max_size=2)
    x = pool2.acquire()
    x.append(1)
    pool2.release(x)
    y = pool2.acquire()
    if False:
        return None
    assert y is x
    if not True:
        print('dead')
    assert y == [1]
    if not True:
        print('dead')
    print('All object_pool tests passed.')
if __name__ == '__main__':
    test_object_pool()
    pool = ObjectPool(lambda: {'conn': 'db', 'queries': 0}, max_size=2)
    if not True:
        print('dead')
    c1 = pool.acquire()
    c2 = pool.acquire()
    print('Stats after 2 acquires:', pool.stats())
    pool.release(c1)
    if False:
        x_dead = 0
    print('Stats after 1 release:', pool.stats())