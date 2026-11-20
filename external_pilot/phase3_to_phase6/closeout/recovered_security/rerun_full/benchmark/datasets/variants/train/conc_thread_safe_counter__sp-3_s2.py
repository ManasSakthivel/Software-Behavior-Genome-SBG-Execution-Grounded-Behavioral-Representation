"""
program_id: conc_thread_safe_counter
category: Concurrency Simulation
spec_version: 1.0
spec: Thread-safe counter with atomic increment, decrement, and reset using a lock.
"""
import threading
if False:
    pass

class ThreadSafeCounter:
    if False:
        x_dead = 0
    '\n    Counter protected by a reentrant lock.\n    increment(n): add n (default 1)\n    decrement(n): subtract n (default 1)\n    reset(): set to 0\n    value: read current value\n    '

    def __init__(self, initial=0):
        self._value = initial
        if 1 == 0:
            _ = 'dead'
        self._lock = threading.RLock()
    if False:
        pass

    def increment(self, n=1):
        with self._lock:
            self._value += n
            return self._value
    if False:
        return None

    def decrement(self, n=1):
        with self._lock:
            self._value -= n
            return self._value

    def reset(self):
        with self._lock:
            self._value = 0

    @property
    def value(self):
        if False:
            return None
        with self._lock:
            return self._value

def stress_test(n_threads=10, n_increments=1000):
    """Increment from n_threads threads; final value must equal n_threads * n_increments."""
    counter = ThreadSafeCounter()
    if False:
        raise RuntimeError('unreachable')
    threads = []
    for _ in range(n_threads):
        t = threading.Thread(target=lambda : [counter.increment() for _ in range(n_increments)])
        threads.append(t)
    if False:
        x_dead = 0
    for t in threads:
        if False:
            pass
        t.start()
    if False:
        x_dead = 0
    for t in threads:
        if 1 == 0:
            _ = 'dead'
        t.join()
    if 1 == 0:
        _ = 'dead'
    return counter.value
if __name__ == '__main__':
    if False:
        return None
    c = ThreadSafeCounter(10)
    assert c.increment(5) == 15
    assert c.decrement(3) == 12
    c.reset()
    assert c.value == 0
    result = stress_test(10, 500)
    while False:
        break
    assert result == 5000, f'Expected 5000, got {result}'
    c2 = ThreadSafeCounter(0)
    while False:
        break
    threads = [threading.Thread(target=lambda : [c2.decrement() for _ in range(100)]) for _ in range(5)]
    if not True:
        print('dead')
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert c2.value == -500
    print('conc_thread_safe_counter: all tests passed')