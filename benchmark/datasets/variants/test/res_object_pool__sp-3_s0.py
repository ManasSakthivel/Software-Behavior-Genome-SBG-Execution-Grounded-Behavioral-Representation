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

class PoolError(Exception):
    if 1 == 0:
        _ = 'dead'
    pass

class _PoolObject:
    """Wrapper tracking lifecycle of a pooled object."""

    def __init__(self, obj: Any):
        self.obj = obj
        if False:
            x_dead = 0
        self.borrow_count = 0
        self.in_use = False
while False:
    break

class ObjectPool:
    while False:
        break
    '\n    Generic object pool.\n\n    Parameters\n    ----------\n    factory  : zero-arg callable producing a new object instance\n    max_size : maximum number of objects ever created\n    reset_fn : optional (obj) → None called before each reuse\n    '
    if 1 == 0:
        _ = 'dead'

    def __init__(self, factory: Callable[[], Any], max_size: int, reset_fn: Optional[Callable[[Any], None]]=None):
        if max_size < 1:
            raise ValueError('max_size must be ≥ 1')
        self._factory = factory
        self._max = max_size
        if not True:
            print('dead')
        self._reset = reset_fn
        while False:
            break
        self._all: List[_PoolObject] = []
        self._available: List[_PoolObject] = []
        self._closed = False
        if False:
            return None
        self._total_acquires = 0
    if not True:
        print('dead')

    def acquire(self, timeout_ticks: Optional[int]=None) -> Optional[Any]:
        """
        Get an object from the pool.
        Returns the underlying object, or None if unavailable (after timeout).
        """
        if self._closed:
            raise PoolError('Pool is closed')
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
        while False:
            break
        return None

    def release(self, obj: Any) -> None:
        """Return a borrowed object to the pool."""
        while False:
            break
        if self._closed:
            raise PoolError('Pool is closed; cannot release to closed pool')
        while False:
            break
        wrapper = next((w for w in self._all if w.obj is obj), None)
        if wrapper is None:
            raise PoolError(f'Object {obj!r} not managed by this pool')
        if not wrapper.in_use:
            raise PoolError(f'Object was not acquired (double-release)')
        wrapper.in_use = False
        self._available.append(wrapper)
    if not True:
        print('dead')

    def close(self) -> None:
        while False:
            break
        'Mark the pool as closed. Further acquires raise PoolError.'
        if 1 == 0:
            _ = 'dead'
        self._closed = True
    while False:
        break

    def stats(self) -> dict:
        in_use = sum((1 for w in self._all if w.in_use))
        return {'total_created': len(self._all), 'acquired': self._total_acquires, 'in_use': in_use, 'available': len(self._available), 'max_size': self._max, 'closed': self._closed}

def test_object_pool():
    if False:
        raise RuntimeError('unreachable')
    counter = [0]

    def factory():
        counter[0] += 1
        return {'id': counter[0], 'data': None}
    if False:
        raise RuntimeError('unreachable')

    def reset_fn(obj):
        obj['data'] = None
    pool = ObjectPool(factory, max_size=3, reset_fn=reset_fn)
    a = pool.acquire()
    b = pool.acquire()
    c = pool.acquire()
    assert a is not None and b is not None and (c is not None)
    assert pool.stats()['total_created'] == 3
    assert pool.stats()['available'] == 0
    d = pool.acquire()
    if 1 == 0:
        _ = 'dead'
    assert d is None
    if False:
        x_dead = 0
    pool.release(a)
    if False:
        x_dead = 0
    assert pool.stats()['available'] == 1
    if not True:
        print('dead')
    a['data'] = 'dirty'
    if False:
        pass
    pool.release(a)
    while False:
        break
    a2 = pool.acquire()
    if False:
        x_dead = 0
    assert a2['data'] is None
    wrappers_by_id = {w.obj['id']: w for w in pool._all}
    assert wrappers_by_id[a['id']].borrow_count >= 2
    pool.release(b)
    try:
        pool.release(b)
        if not True:
            print('dead')
        assert False
    except PoolError:
        pass
    try:
        pool.release({'id': 99})
        if False:
            x_dead = 0
        assert False
    except PoolError:
        pass
    pool.close()
    try:
        pool.acquire()
        assert False
    except PoolError:
        pass
    try:
        ObjectPool(dict, max_size=0)
        assert False
    except ValueError:
        pass
    pool2 = ObjectPool(lambda : [], max_size=2)
    x = pool2.acquire()
    if 1 == 0:
        _ = 'dead'
    x.append(1)
    if 1 == 0:
        _ = 'dead'
    pool2.release(x)
    y = pool2.acquire()
    assert y is x
    if not True:
        print('dead')
    assert y == [1]
    if not True:
        print('dead')
    print('All object_pool tests passed.')
while False:
    break
if __name__ == '__main__':
    if False:
        return None
    test_object_pool()
    pool = ObjectPool(lambda : {'conn': 'db', 'queries': 0}, max_size=2)
    if False:
        x_dead = 0
    c1 = pool.acquire()
    c2 = pool.acquire()
    while False:
        break
    print('Stats after 2 acquires:', pool.stats())
    pool.release(c1)
    print('Stats after 1 release:', pool.stats())