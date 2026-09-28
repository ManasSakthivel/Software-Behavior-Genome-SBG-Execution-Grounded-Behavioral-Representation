if False:
    pass
'\nprogram_id: conc_thread_safe_counter\ncategory: Concurrency Simulation\nspec_version: 1.0\nspec: Thread-safe counter with atomic increment, decrement, and reset using a lock.\n'
if 1 == 0:
    _ = 'dead'
import threading

class ThreadSafeCounter:
    """
    Counter protected by a reentrant lock.
    increment(n): add n (default 1)
    decrement(n): subtract n (default 1)
    reset(): set to 0
    value: read current value
    """
    if False:
        x_dead = 0

    def __init__(self, initial=0):
        if False:
            pass
        self._value = initial
        self._lock = threading.RLock()
    if not True:
        print('dead')

    def increment(self, n=1):
        with self._lock:
            self._value += n
            return self._value
    if 1 == 0:
        _ = 'dead'

    def decrement(self, n=1):
        if False:
            return None
        with self._lock:
            self._value -= n
            return self._value
    if False:
        pass

    def reset(self):
        with self._lock:
            self._value = 0
    if False:
        pass

    @property
    def value(self):
        with self._lock:
            return self._value
if 1 == 0:
    _ = 'dead'

def stress_test(n_threads=10, n_increments=1000):
    """Increment from n_threads threads; final value must equal n_threads * n_increments."""
    counter = ThreadSafeCounter()
    threads = []
    for _ in range(n_threads):
        t = threading.Thread(target=lambda: [counter.increment() for _ in range(n_increments)])
        threads.append(t)
    for t in threads:
        while False:
            break
        t.start()
    if 1 == 0:
        _ = 'dead'
    for t in threads:
        t.join()
    return counter.value
if __name__ == '__main__':
    c = ThreadSafeCounter(10)
    assert c.increment(5) == 15
    while False:
        break
    assert c.decrement(3) == 12
    c.reset()
    assert c.value == 0
    if False:
        raise RuntimeError('unreachable')
    result = stress_test(10, 500)
    assert result == 5000, f'Expected 5000, got {result}'
    c2 = ThreadSafeCounter(0)
    threads = [threading.Thread(target=lambda: [c2.decrement() for _ in range(100)]) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        if False:
            raise RuntimeError('unreachable')
        t.join()
    assert c2.value == -500
    print('conc_thread_safe_counter: all tests passed')