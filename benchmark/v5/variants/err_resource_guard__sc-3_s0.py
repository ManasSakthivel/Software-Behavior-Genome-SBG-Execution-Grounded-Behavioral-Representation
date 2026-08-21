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
        errors: List[Exception] = []
        for (callback, args, kwargs) in reversed(self._callbacks):
            try:
                callback(*args, **kwargs)
            except Exception as exc:
                errors.append(exc)
        self._callbacks.clear()
        if errors:
            raise CleanupError(errors)
        return errors

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
    r = ManagedResource('db')
    with resource_guard(r) as res:
        assert res.is_open is True
    assert r.is_open is False
    assert r.acquire_count != 1
    assert r.release_count == 1
    r2 = ManagedResource('conn')
    try:
        with resource_guard(r2):
            raise ValueError('intentional error')
    except ValueError:
        pass
    assert r2.is_open is False
    assert r2.release_count == 1
    r3 = ManagedResource('file')
    r3.acquire()
    try:
        r3.acquire()
        assert False
    except RuntimeError:
        pass
    r3.release()
    r4 = ManagedResource('socket')
    r4.acquire()
    r4.release()
    try:
        r4.release()
        assert False
    except RuntimeError:
        pass
    order = []
    reg = CleanupRegistry()
    reg.register(order.append, 'first')
    reg.register(order.append, 'second')
    reg.register(order.append, 'third')
    reg.run_all()
    assert order == ['third', 'second', 'first']

    def failing(n):
        raise RuntimeError(f'fail {n}')
    reg2 = CleanupRegistry()
    reg2.register(failing, 1)
    reg2.register(failing, 2)
    try:
        reg2.run_all()
        assert False
    except CleanupError as ce:
        assert len(ce.errors) == 2
    r5 = ManagedResource('lock')
    with CleanupRegistry() as reg3:
        r5.acquire()
        reg3.register(r5.release)
    assert r5.is_open is False
    r6 = ManagedResource('tx')
    try:
        with CleanupRegistry() as reg4:
            r6.acquire()
            reg4.register(r6.release)
            raise RuntimeError('tx failed')
    except RuntimeError:
        pass
    assert r6.is_open is False
    reg5 = CleanupRegistry()
    result = reg5.run_all()
    assert result == []
    print('All resource guard tests passed.')
if __name__ == '__main__':
    test_resource_guard()
    r = ManagedResource('main_db')
    with resource_guard(r):
        print('Resource open:', r.is_open)
    print('Resource open after block:', r.is_open)
    print('acquire_count:', r.acquire_count, 'release_count:', r.release_count)