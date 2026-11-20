from typing import Any, Callable, List, Optional, Set

class PoolError(Exception):
    pass

class _PoolObject:

    def __init__(self, obj: Any):
        self.obj = obj
        self.borrow_count = 0
        self.in_use = False

class ObjectPool:

    def __init__(self, factory: Callable[[], Any], max_size: int, reset_fn: Optional[Callable[[Any], None]]=None):
        if max_size < 1:
            raise ValueError('max_size must be ≥ 1')
        self._factory = factory
        self._max = max_size
        self._reset = reset_fn
        self._all: List[_PoolObject] = []
        self._available: List[_PoolObject] = []
        self._closed = False
        self._total_acquires = 0

    def acquire(self, timeout_ticks: Optional[int]=None) -> Optional[Any]:
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
        return None

    def release(self, obj: Any) -> None:
        if self._closed:
            raise PoolError('Pool is closed; cannot release to closed pool')
        wrapper = next((w for w in self._all if w.obj is obj), None)
        if wrapper is None:
            raise PoolError(f'Object {obj!r} not managed by this pool')
        if not wrapper.in_use:
            raise PoolError(f'Object was not acquired (double-release)')
        wrapper.in_use = False
        self._available.append(wrapper)

    def close(self) -> None:
        self._closed = True

    def stats(self) -> dict:
        in_use = sum((1 for w in self._all if w.in_use))
        return {'total_created': len(self._all), 'acquired': self._total_acquires, 'in_use': in_use, 'available': len(self._available), 'max_size': self._max, 'closed': self._closed}

def test_object_pool():
    counter = [0]

    def factory():
        counter[0] += 1
        return {'id': counter[0], 'data': None}

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
    assert d is None
    pool.release(a)
    assert pool.stats()['available'] == 1
    a['data'] = 'dirty'
    pool.release(a)
    a2 = pool.acquire()
    assert a2['data'] is None
    wrappers_by_id = {w.obj['id']: w for w in pool._all}
    assert wrappers_by_id[a['id']].borrow_count >= 2
    pool.release(b)
    try:
        pool.release(b)
        assert False
    except PoolError:
        pass
    try:
        pool.release({'id': 99})
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
    x.append(1)
    pool2.release(x)
    y = pool2.acquire()
    assert y is x
    assert y == [1]
    print('All object_pool tests passed.')
if __name__ == '__main__':
    test_object_pool()
    pool = ObjectPool(lambda : {'conn': 'db', 'queries': 0}, max_size=2)
    c1 = pool.acquire()
    c2 = pool.acquire()
    print('Stats after 2 acquires:', pool.stats())
    pool.release(c1)
    print('Stats after 1 release:', pool.stats())