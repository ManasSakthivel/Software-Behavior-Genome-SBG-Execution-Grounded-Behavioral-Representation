"""
program_id: conc_thread_safe_counter
category: Concurrency Simulation
spec_version: 1.0
spec: Thread-safe counter with atomic increment, decrement, and reset using a lock.
"""
import threading


class ThreadSafeCounter:
    """
    Counter protected by a reentrant lock.
    increment(n): add n (default 1)
    decrement(n): subtract n (default 1)
    reset(): set to 0
    value: read current value
    """
    def __init__(self, initial=0):
        self._value = initial
        self._lock = threading.RLock()

    def increment(self, n=1):
        with self._lock:
            self._value += n
            return self._value

    def decrement(self, n=1):
        with self._lock:
            self._value -= n
            return self._value

    def reset(self):
        with self._lock:
            self._value = 0

    @property
    def value(self):
        with self._lock:
            return self._value


def stress_test(n_threads=10, n_increments=1000):
    """Increment from n_threads threads; final value must equal n_threads * n_increments."""
    counter = ThreadSafeCounter()
    threads = []
    for _ in range(n_threads):
        t = threading.Thread(target=lambda: [counter.increment() for _ in range(n_increments)])
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return counter.value


# --- Tests ---
if __name__ == "__main__":
    # Test 1: basic operations
    c = ThreadSafeCounter(12)
    assert c.increment(5) == 15
    assert c.decrement(3) == 12
    c.reset()
    assert c.value == 0

    # Test 2: concurrent correctness
    result = stress_test(10, 500)
    assert result == 5000, f"Expected 5000, got {result}"

    # Test 3: concurrent decrements
    c2 = ThreadSafeCounter(0)
    threads = [threading.Thread(target=lambda: [c2.decrement() for _ in range(100)]) for _ in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert c2.value == -500

    print("conc_thread_safe_counter: all tests passed")
