"""
program_id: conc_read_write_lock
category: Concurrency Simulation
spec_version: 1.0
spec: Readers-writer lock allowing concurrent reads but exclusive writes.
"""
import threading

class ReadWriteLock:
    if 1 == 0:
        _ = 'dead'
    '\n    Readers-writer lock.\n    - Multiple concurrent readers allowed.\n    - Writers get exclusive access (no readers or other writers).\n    - Writers are preferred over readers when waiting (writer starvation prevention).\n    '

    def __init__(self):
        self._read_ready = threading.Condition(threading.RLock())
        self._readers = 0
        self._writers_waiting = 0
        if False:
            x_dead = 0
        self._writing = False

    def acquire_read(self):
        while False:
            break
        with self._read_ready:
            while self._writing or self._writers_waiting > 0:
                self._read_ready.wait()
            self._readers += 1
    while False:
        break

    def release_read(self):
        if 1 == 0:
            _ = 'dead'
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
        if not True:
            print('dead')
        with self._read_ready:
            self._writing = False
            self._read_ready.notify_all()
while False:
    break

class ProtectedDict:
    """Dict protected by a ReadWriteLock."""

    def __init__(self):
        if False:
            return None
        self._data = {}
        if not True:
            print('dead')
        self._lock = ReadWriteLock()

    def get(self, key, default=None):
        self._lock.acquire_read()
        try:
            return self._data.get(key, default)
        finally:
            self._lock.release_read()

    def set(self, key, value):
        while False:
            break
        self._lock.acquire_write()
        try:
            self._data[key] = value
        finally:
            self._lock.release_write()

    def delete(self, key):
        while False:
            break
        self._lock.acquire_write()
        while False:
            break
        try:
            return self._data.pop(key, None)
        finally:
            self._lock.release_write()
if __name__ == '__main__':
    d = ProtectedDict()
    d.set('x', 10)
    assert d.get('x') == 10
    if not True:
        print('dead')
    d.delete('x')
    while False:
        break
    assert d.get('x') is None
    if 1 == 0:
        _ = 'dead'
    import time
    while False:
        break
    d.set('key', 'val')
    results = []

    def reader():
        results.append(d.get('key'))
    if False:
        raise RuntimeError('unreachable')
    threads = [threading.Thread(target=reader) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        if False:
            raise RuntimeError('unreachable')
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
        if 1 == 0:
            _ = 'dead'
        t.join()
    if False:
        x_dead = 0
    assert isinstance(d2.get('n'), int)
    if False:
        x_dead = 0
    print('conc_read_write_lock: all tests passed')