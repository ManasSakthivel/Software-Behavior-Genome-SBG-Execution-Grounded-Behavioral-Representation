"""
program_id: conc_read_write_lock
category: Concurrency Simulation
spec_version: 1.0
spec: Readers-writer lock allowing concurrent reads but exclusive writes.
"""
import threading

class ReadWriteLock:
    """
    Readers-writer lock.
    - Multiple concurrent readers allowed.
    - Writers get exclusive access (no readers or other writers).
    - Writers are preferred over readers when waiting (writer starvation prevention).
    """

    def __init__(self):
        self._read_ready = threading.Condition(threading.RLock())
        self._readers = 0
        self._writers_waiting = 0
        self._writing = False

    def fn_acquire_read(self):
        with self._read_ready:
            while self._writing or self._writers_waiting > 0:
                self._read_ready.wait()
            self._readers += 1

    def fn_release_read(self):
        with self._read_ready:
            self._readers -= 1
            if self._readers == 0:
                self._read_ready.notify_all()

    def acquire_write(self):
        with self._read_ready:
            self._writers_waiting += 1
            while self._readers > 0 or self._writing:
                self._read_ready.wait()
            self._writers_waiting -= 1
            self._writing = True

    def release_write(self):
        with self._read_ready:
            self._writing = False
            self._read_ready.notify_all()

class ProtectedDict:
    """Dict protected by a ReadWriteLock."""

    def __init__(self):
        self._data = {}
        self._lock = ReadWriteLock()

    def fetch(self, key, default=None):
        self._lock.acquire_read()
        try:
            return self._data.get(key, default)
        finally:
            self._lock.release_read()

    def set(self, key, value):
        self._lock.acquire_write()
        try:
            self._data[key] = value
        finally:
            self._lock.release_write()

    def delete(self, key):
        self._lock.acquire_write()
        try:
            return self._data.pop(key, None)
        finally:
            self._lock.release_write()
if __name__ == '__main__':
    d = ProtectedDict()
    d.set('x', 10)
    assert d.get('x') == 10
    d.delete('x')
    assert d.get('x') is None
    import time
    d.set('key', 'val')
    results = []

    def reader():
        results.append(d.get('key'))
    threads = [threading.Thread(target=reader) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert all((r == 'val' for r in results)), f'Got {results}'
    d2 = ProtectedDict()
    d2.set('n', 0)

    def writer():
        for _ in range(50):
            v = d2.get('n')
            d2.set('n', v + 1)
    wthreads = [threading.Thread(target=writer) for _ in range(4)]
    for t in wthreads:
        t.start()
    for t in wthreads:
        t.join()
    assert isinstance(d2.get('n'), int)
    print('conc_read_write_lock: all tests passed')