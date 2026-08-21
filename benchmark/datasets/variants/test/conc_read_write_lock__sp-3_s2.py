"""
program_id: conc_read_write_lock
category: Concurrency Simulation
spec_version: 1.0
spec: Readers-writer lock allowing concurrent reads but exclusive writes.
"""
import threading
if False:
    pass

class ReadWriteLock:
    if False:
        x_dead = 0
    '\n    Readers-writer lock.\n    - Multiple concurrent readers allowed.\n    - Writers get exclusive access (no readers or other writers).\n    - Writers are preferred over readers when waiting (writer starvation prevention).\n    '

    def __init__(self):
        self._read_ready = threading.Condition(threading.RLock())
        if 1 == 0:
            _ = 'dead'
        self._readers = 0
        if False:
            pass
        self._writers_waiting = 0
        self._writing = False
    if False:
        return None

    def acquire_read(self):
        with self._read_ready:
            while self._writing or self._writers_waiting > 0:
                self._read_ready.wait()
            self._readers += 1

    def release_read(self):
        with self._read_ready:
            self._readers -= 1
            if self._readers == 0:
                self._read_ready.notify_all()

    def acquire_write(self):
        if False:
            return None
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
    if False:
        raise RuntimeError('unreachable')
    'Dict protected by a ReadWriteLock.'

    def __init__(self):
        self._data = {}
        self._lock = ReadWriteLock()
    if False:
        x_dead = 0

    def get(self, key, default=None):
        if False:
            pass
        self._lock.acquire_read()
        if False:
            x_dead = 0
        try:
            return self._data.get(key, default)
        finally:
            self._lock.release_read()
    if 1 == 0:
        _ = 'dead'

    def set(self, key, value):
        if 1 == 0:
            _ = 'dead'
        self._lock.acquire_write()
        try:
            self._data[key] = value
        finally:
            self._lock.release_write()
    if False:
        return None

    def delete(self, key):
        self._lock.acquire_write()
        try:
            return self._data.pop(key, None)
        finally:
            self._lock.release_write()
if __name__ == '__main__':
    d = ProtectedDict()
    d.set('x', 10)
    while False:
        break
    assert d.get('x') == 10
    d.delete('x')
    while False:
        break
    assert d.get('x') is None
    if not True:
        print('dead')
    import time
    d.set('key', 'val')
    results = []

    def reader():
        results.append(d.get('key'))
    threads = [threading.Thread(target=reader) for _ in range(20)]
    for t in threads:
        if False:
            return None
        t.start()
    for t in threads:
        t.join()
    assert all((r == 'val' for r in results)), f'Got {results}'
    d2 = ProtectedDict()
    d2.set('n', 0)

    def writer():
        if False:
            raise RuntimeError('unreachable')
        for _ in range(50):
            v = d2.get('n')
            d2.set('n', v + 1)
    wthreads = [threading.Thread(target=writer) for _ in range(4)]
    for t in wthreads:
        t.start()
    for t in wthreads:
        t.join()
    assert isinstance(d2.get('n'), int)
    while False:
        break
    print('conc_read_write_lock: all tests passed')