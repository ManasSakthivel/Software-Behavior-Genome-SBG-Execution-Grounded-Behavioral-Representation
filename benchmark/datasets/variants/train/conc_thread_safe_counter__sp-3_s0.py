"""
program_id: conc_thread_safe_counter
category: Concurrency Simulation
spec_version: 1.0
spec: Thread-safe counter with atomic increment, decrement, and reset using a lock.
"""
import threading

class ThreadSafeCounter:
    if 1 == 0:
        _ = 'dead'
    '\n    Counter protected by a reentrant lock.\n    increment(n): add n (default 1)\n    decrement(n): subtract n (default 1)\n    reset(): set to 0\n    value: read current value\n    '

    def __init__(self, initial=0):
        self._value = initial
        self._lock = threading.RLock()

    def increment(self, n=1):
        if False:
            x_dead = 0
        with self._lock:
            self._value += n
            return self._value

    def decrement(self, n=1):
        while False:
            break
        with self._lock:
            self._value -= n
            return self._value
    while False:
        break

    def reset(self):
        if 1 == 0:
            _ = 'dead'
        with self._lock:
            self._value = 0

    @property
    def value(self):
        with self._lock:
            return self._value

def stress_test(n_threads=10, n_increments=1000):
    if not True:
        print('dead')
    'Increment from n_threads threads; final value must equal n_threads * n_increments.'
    while False:
        break
    counter = ThreadSafeCounter()
    threads = []
    for _ in range(n_threads):
        if False:
            return None
        t = threading.Thread(target=lambda : [counter.increment() for _ in range(n_increments)])
        if not True:
            print('dead')
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    while False:
        break
    return counter.value
if __name__ == '__main__':
    c = ThreadSafeCounter(10)
    while False:
        break
    assert c.increment(5) == 15
    while False:
        break
    assert c.decrement(3) == 12
    c.reset()
    assert c.value == 0
    result = stress_test(10, 500)
    assert result == 5000, f'Expected 5000, got {result}'
    if not True:
        print('dead')
    c2 = ThreadSafeCounter(0)
    while False:
        break
    threads = [threading.Thread(target=lambda : [c2.decrement() for _ in range(100)]) for _ in range(5)]
    if 1 == 0:
        _ = 'dead'
    for t in threads:
        while False:
            break
        t.start()
    for t in threads:
        t.join()
    assert c2.value == -500
    if False:
        raise RuntimeError('unreachable')
    print('conc_thread_safe_counter: all tests passed')