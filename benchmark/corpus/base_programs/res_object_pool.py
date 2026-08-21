# program_id: res_object_pool
# category: resource_management
# spec_version: 1.0

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
    pass


class _PoolObject:
    """Wrapper tracking lifecycle of a pooled object."""
    def __init__(self, obj: Any):
        self.obj = obj
        self.borrow_count = 0
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

    def __init__(self,
                 factory: Callable[[], Any],
                 max_size: int,
                 reset_fn: Optional[Callable[[Any], None]] = None):
        if max_size < 1:
            raise ValueError("max_size must be ≥ 1")
        self._factory = factory
        self._max = max_size
        self._reset = reset_fn
        self._all: List[_PoolObject] = []   # all ever-created
        self._available: List[_PoolObject] = []  # idle objects
        self._closed = False
        self._total_acquires = 0

    def acquire(self, timeout_ticks: Optional[int] = None) -> Optional[Any]:
        """
        Get an object from the pool.
        Returns the underlying object, or None if unavailable (after timeout).
        """
        if self._closed:
            raise PoolError("Pool is closed")

        # Prefer returning an idle object
        if self._available:
            wrapper = self._available.pop()
            if self._reset:
                self._reset(wrapper.obj)
            wrapper.in_use = True
            wrapper.borrow_count += 1
            self._total_acquires += 1
            return wrapper.obj

        # Create a new object if under limit
        if len(self._all) < self._max:
            wrapper = _PoolObject(self._factory())
            wrapper.in_use = True
            wrapper.borrow_count = 1
            self._all.append(wrapper)
            self._total_acquires += 1
            return wrapper.obj

        # Pool exhausted
        return None

    def release(self, obj: Any) -> None:
        """Return a borrowed object to the pool."""
        if self._closed:
            raise PoolError("Pool is closed; cannot release to closed pool")
        wrapper = next((w for w in self._all if w.obj is obj), None)
        if wrapper is None:
            raise PoolError(f"Object {obj!r} not managed by this pool")
        if not wrapper.in_use:
            raise PoolError(f"Object was not acquired (double-release)")
        wrapper.in_use = False
        self._available.append(wrapper)

    def close(self) -> None:
        """Mark the pool as closed. Further acquires raise PoolError."""
        self._closed = True

    def stats(self) -> dict:
        in_use = sum(1 for w in self._all if w.in_use)
        return {
            "total_created": len(self._all),
            "acquired":      self._total_acquires,
            "in_use":        in_use,
            "available":     len(self._available),
            "max_size":      self._max,
            "closed":        self._closed,
        }


# ---------- tests ----------

def test_object_pool():
    # Factory: simple counter objects
    counter = [0]
    def factory():
        counter[0] += 1
        return {"id": counter[0], "data": None}

    def reset_fn(obj):
        obj["data"] = None   # clear state on reuse

    pool = ObjectPool(factory, max_size=3, reset_fn=reset_fn)

    # Test 1: acquire creates objects up to max
    a = pool.acquire()
    b = pool.acquire()
    c = pool.acquire()
    assert a is not None and b is not None and c is not None
    assert pool.stats()["total_created"] == 3
    assert pool.stats()["available"] == 0

    # Test 2: acquire beyond max returns None
    d = pool.acquire()
    assert d is None

    # Test 3: release makes object available
    pool.release(a)
    assert pool.stats()["available"] == 1

    # Test 4: re-acquire the released object (reset called)
    a["data"] = "dirty"   # simulate usage
    pool.release(a)
    a2 = pool.acquire()
    assert a2["data"] is None   # reset_fn cleared it

    # Test 5: borrow_count tracked
    wrappers_by_id = {w.obj["id"]: w for w in pool._all}
    assert wrappers_by_id[a["id"]].borrow_count >= 2

    # Test 6: double release raises PoolError
    pool.release(b)
    try:
        pool.release(b)
        assert False
    except PoolError:
        pass

    # Test 7: release unknown object raises PoolError
    try:
        pool.release({"id": 99})
        assert False
    except PoolError:
        pass

    # Test 8: close pool
    pool.close()
    try:
        pool.acquire()
        assert False
    except PoolError:
        pass

    # Test 9: invalid max_size raises
    try:
        ObjectPool(dict, max_size=0)
        assert False
    except ValueError:
        pass

    # Test 10: pool without reset_fn works fine
    pool2 = ObjectPool(lambda: [], max_size=2)
    x = pool2.acquire()
    x.append(1)
    pool2.release(x)
    y = pool2.acquire()
    assert y is x   # same object reused (not reset)
    assert y == [1]

    print("All object_pool tests passed.")


if __name__ == "__main__":
    test_object_pool()
    pool = ObjectPool(lambda: {"conn": "db", "queries": 0}, max_size=2)
    c1 = pool.acquire()
    c2 = pool.acquire()
    print("Stats after 2 acquires:", pool.stats())
    pool.release(c1)
    print("Stats after 1 release:", pool.stats())
