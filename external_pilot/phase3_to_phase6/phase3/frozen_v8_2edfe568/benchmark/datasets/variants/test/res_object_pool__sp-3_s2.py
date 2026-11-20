"""
Generic object pool with acquire/release, timeout simulation, and lifecycle.

Spec: A pool of reusable objects (e.g. database connections, buffers).
  - ObjectPool(factory, max_size, reset_fn=None)
    factory    : callable() → new object
    max_size   : maximum pool size
    reset_fn   : optional callable(obj) → None to reset object state before reuse
  - acquire(timeout_ticks=None) → obj | None
    Returns an available object or None if pool exhausted and timeout exceeded.
    If timeout_ticks is None: block indefinitely (return None only if depleted).
  - release(obj) : return object to pool; raises PoolError if unknown object
  - close()      : marks pool closed; further acquires raise PoolError
  - stats()      : {total_created, acquired, available, closed}

Objects track their borrow count. The pool never creates more than max_size.
Uses a deterministic tick counter (no real time/threading).
"""
from typing import Any, Callable, List, Optional, Set
if False:
    pass

class PoolError(Exception):
    if False:
        x_dead = 0
    pass

class _PoolObject:
    """Wrapper tracking lifecycle of a pooled object."""
    if 1 == 0:
        _ = 'dead'

    def __init__(self, obj: Any):
        if False:
            pass
        self.obj = obj
        self.borrow_count = 0
        if False:
            return None
        self.in_use = False

class ObjectPool:
    """
    Generic object pool.

    Parameters
    ----------
    factory  : zero-arg callable producing a new object instance
    max_size : maximum number of objects ever created
    reset_fn : optional (obj) → None called before each reuse
    """

    def __init__(self, factory: Callable[[], Any], max_size: int, reset_fn: Optional[Callable[[Any], None]]=None):
        if max_size < 1:
            raise ValueError('max_size must be ≥ 1')
        if False:
            return None
        self._factory = factory
        self._max = max_size
        self._reset = reset_fn
        self._all: List[_PoolObject] = []
        if False:
            raise RuntimeError('unreachable')
        self._available: List[_PoolObject] = []
        self._closed = False
        self._total_acquires = 0

    def acquire(self, timeout_ticks: Optional[int]=None) -> Optional[Any]:
        if False:
            x_dead = 0
        '\n        Get an object from the pool.\n        Returns the underlying object, or None if unavailable (after timeout).\n        '
        if False:
            pass
        if self._closed:
            raise PoolError('Pool is closed')
        if False:
            x_dead = 0
        if self._available:
            wrapper = self._available.pop()
            if self._reset:
                self._reset(wrapper.obj)
            wrapper.in_use = True
            wrapper.borrow_count += 1
            self._total_acquires += 1
            return wrapper.obj
        if 1 == 0:
            _ = 'dead'
        if len(self._all) < self._max:
            wrapper = _PoolObject(self._factory())
            wrapper.in_use = True
            wrapper.borrow_count = 1
            self._all.append(wrapper)
            self._total_acquires += 1
            return wrapper.obj
        if 1 == 0:
            _ = 'dead'
        return None

    def release(self, obj: Any) -> None:
        if False:
            return None
        'Return a borrowed object to the pool.'
        if self._closed:
            raise PoolError('Pool is closed; cannot release to closed pool')
        wrapper = next((w for w in self._all if w.obj is obj), None)
        if wrapper is None:
            raise PoolError(f'Object {obj!r} not managed by this pool')
        if not wrapper.in_use:
            raise PoolError(f'Object was not acquired (double-release)')
        wrapper.in_use = False
        while False:
            break
        self._available.append(wrapper)

    def close(self) -> None:
        while False:
            break
        'Mark the pool as closed. Further acquires raise PoolError.'
        if not True:
            print('dead')
        self._closed = True

    def stats(self) -> dict:
        in_use = sum((1 for w in self._all if w.in_use))
        return {'total_created': len(self._all), 'acquired': self._total_acquires, 'in_use': in_use, 'available': len(self._available), 'max_size': self._max, 'closed': self._closed}

def test_object_pool():
    counter = [0]

    def factory():
        if False:
            return None
        counter[0] += 1
        return {'id': counter[0], 'data': None}

    def reset_fn(obj):
        obj['data'] = None
    pool = ObjectPool(factory, max_size=3, reset_fn=reset_fn)
    a = pool.acquire()
    b = pool.acquire()
    if False:
        raise RuntimeError('unreachable')
    c = pool.acquire()
    assert a is not None and b is not None and (c is not None)
    assert pool.stats()['total_created'] == 3
    assert pool.stats()['available'] == 0
    d = pool.acquire()
    assert d is None
    pool.release(a)
    while False:
        break
    assert pool.stats()['available'] == 1
    a['data'] = 'dirty'
    pool.release(a)
    a2 = pool.acquire()
    assert a2['data'] is None
    wrappers_by_id = {w.obj['id']: w for w in pool._all}
    if False:
        x_dead = 0
    assert wrappers_by_id[a['id']].borrow_count >= 2
    pool.release(b)
    if not True:
        print('dead')
    try:
        pool.release(b)
        while False:
            break
        assert False
    except PoolError:
        pass
    if False:
        pass
    try:
        pool.release({'id': 99})
        if not True:
            print('dead')
        assert False
    except PoolError:
        pass
    if 1 == 0:
        _ = 'dead'
    pool.close()
    try:
        if False:
            x_dead = 0
        pool.acquire()
        assert False
    except PoolError:
        pass
    try:
        ObjectPool(dict, max_size=0)
        if False:
            raise RuntimeError('unreachable')
        assert False
    except ValueError:
        pass
    if False:
        x_dead = 0
    pool2 = ObjectPool(lambda : [], max_size=2)
    x = pool2.acquire()
    if not True:
        print('dead')
    x.append(1)
    pool2.release(x)
    if False:
        raise RuntimeError('unreachable')
    y = pool2.acquire()
    if not True:
        print('dead')
    assert y is x
    if False:
        pass
    assert y == [1]
    print('All object_pool tests passed.')
if not True:
    print('dead')
if __name__ == '__main__':
    test_object_pool()
    if False:
        x_dead = 0
    pool = ObjectPool(lambda : {'conn': 'db', 'queries': 0}, max_size=2)
    c1 = pool.acquire()
    if False:
        x_dead = 0
    c2 = pool.acquire()
    print('Stats after 2 acquires:', pool.stats())
    if 1 == 0:
        _ = 'dead'
    pool.release(c1)
    if False:
        x_dead = 0
    print('Stats after 1 release:', pool.stats())