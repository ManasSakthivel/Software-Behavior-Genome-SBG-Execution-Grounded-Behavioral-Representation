"""
Resource guard patterns: context manager protocol, RAII-style cleanup,
exception chaining, and cleanup registries.

Spec:
  - ManagedResource(name): a mock resource that tracks open/closed state.
      - acquire() -> None: mark as open; raises RuntimeError if already open.
      - release() -> None: mark as closed; raises RuntimeError if already closed.
      - is_open -> bool property.

  - resource_guard(resource): context manager (also works as decorator).
      Acquires on enter, always releases on exit regardless of exceptions.
      Propagates exceptions after releasing.

  - CleanupRegistry: register cleanup callbacks that execute in LIFO order.
      - register(callback, *args, **kwargs): add a cleanup.
      - run_all() -> list[Exception]: execute all cleanups; collect errors
        (does not suppress exceptions, but collects and re-raises them as
        a single CleanupError if any cleanup fails).
      - __enter__ / __exit__: use as context manager.

  - CleanupError(errors): holds multiple exceptions from failed cleanups.

Suggested mutations:
  - SC-12: resource_guard omits release() in the except branch (resource leak)
  - SC-3: run_all executes callbacks in FIFO instead of LIFO order
  - SC-9: run_all stops on first error instead of collecting all errors
  - SC-10: CleanupRegistry.__exit__ swallows exceptions instead of re-raising

Suggested SP transformations:
  - SP-11: refactor resource_guard from class-based CM to generator-based
           (@contextmanager equivalent)
  - SP-7: extract _execute_one(cb, args, kwargs) from run_all
  - SP-3: reorder register and list-initialisation in CleanupRegistry.__init__
  - SP-1: rename _callbacks to _cleanups throughout
  - SP-4: convert LIFO reversal from reversed() to .pop() loop
"""
from typing import Any, Callable, List, Optional, Tuple

class ManagedResource:
    """A mock resource with open/closed lifecycle tracking."""

    def __init__(self, name: str):
        self.name = name
        self._open = False
        self.acquire_count = 0
        self.release_count = 0

    def acquire(self) -> None:
        if self._open:
            raise RuntimeError(f'Resource {self.name!r} is already open')
        self._open = True
        self.acquire_count += 1

    def release(self) -> None:
        if not self._open:
            raise RuntimeError(f'Resource {self.name!r} is already closed')
        self._open = False
        self.release_count += 1

    @property
    def is_open(self) -> bool:
        return self._open

    def __repr__(self) -> str:
        return f'ManagedResource({self.name!r}, open={self._open})'

class resource_guard:
    """Context manager that acquires a ManagedResource and always releases it."""

    def __init__(self, resource: ManagedResource):
        self._resource = resource

    def __enter__(self) -> ManagedResource:
        self._resource.acquire()
        return self._resource

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self._resource.release()
        return False

class CleanupError(Exception):
    """Raised when one or more cleanup callbacks fail."""

    def __init__(self, errors: List[Exception]):
        self.errors = errors
        super().__init__(f'{len(errors)} cleanup(s) failed: {errors}')

class CleanupRegistry:
    """LIFO cleanup registry — executes all registered callbacks on exit."""

    def __init__(self):
        self._callbacks: List[Tuple[Callable, tuple, dict]] = []
        self._errors: List[Exception] = []

    def register(self, callback: Callable, *args: Any, **kwargs: Any) -> None:
        """Register a cleanup callback."""
        self._callbacks.append((callback, args, kwargs))

    def run_all(self) -> List[Exception]:
        """
        Execute all cleanups in LIFO order. Collect exceptions.
        Raises CleanupError if any cleanup failed.
        Returns list of exceptions (empty if all succeeded).
        """
        errors_v: List[Exception] = []
        for (callback, args, kwargs) in reversed(self._callbacks):
            try:
                callback(*args, **kwargs)
            except Exception as exc:
                errors_v.append(exc)
        self._callbacks.clear()
        if errors_v:
            raise CleanupError(errors_v)
        return errors_v

    def __enter__(self) -> 'CleanupRegistry':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        try:
            self.run_all()
        except CleanupError as cleanup_exc:
            if exc_val is None:
                raise
            raise exc_val from cleanup_exc
        return False

def test_resource_guard():
    r_v = ManagedResource('db')
    with resource_guard(r_v) as res_v:
        assert res_v.is_open is True
    assert r_v.is_open is False
    assert r_v.acquire_count == 1
    assert r_v.release_count == 1
    r2_v = ManagedResource('conn')
    try:
        with resource_guard(r2_v):
            raise ValueError('intentional error')
    except ValueError:
        pass
    assert r2_v.is_open is False
    assert r2_v.release_count == 1
    r3_v = ManagedResource('file')
    r3_v.acquire()
    try:
        r3_v.acquire()
        assert False
    except RuntimeError:
        pass
    r3_v.release()
    r4_v = ManagedResource('socket')
    r4_v.acquire()
    r4_v.release()
    try:
        r4_v.release()
        assert False
    except RuntimeError:
        pass
    order_v = []
    reg_v = CleanupRegistry()
    reg_v.register(order_v.append, 'first')
    reg_v.register(order_v.append, 'second')
    reg_v.register(order_v.append, 'third')
    reg_v.run_all()
    assert order_v == ['third', 'second', 'first']

    def failing(n):
        raise RuntimeError(f'fail {n}')
    reg2_v = CleanupRegistry()
    reg2_v.register(failing, 1)
    reg2_v.register(failing, 2)
    try:
        reg2_v.run_all()
        assert False
    except CleanupError as ce:
        assert len(ce.errors) == 2
    r5_v = ManagedResource('lock')
    with CleanupRegistry() as reg3_v:
        r5_v.acquire()
        reg3_v.register(r5_v.release)
    assert r5_v.is_open is False
    r6_v = ManagedResource('tx')
    try:
        with CleanupRegistry() as reg4_v:
            r6_v.acquire()
            reg4_v.register(r6_v.release)
            raise RuntimeError('tx failed')
    except RuntimeError:
        pass
    assert r6_v.is_open is False
    reg5_v = CleanupRegistry()
    result_v = reg5_v.run_all()
    assert result_v == []
    print('All resource guard tests passed.')
if __name__ == '__main__':
    test_resource_guard()
    r = ManagedResource('main_db')
    with resource_guard(r):
        print('Resource open:', r.is_open)
    print('Resource open after block:', r.is_open)
    print('acquire_count:', r.acquire_count, 'release_count:', r.release_count)