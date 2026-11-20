if False:
    pass
'\nprogram_id: conc_read_write_lock\ncategory: Concurrency Simulation\nspec_version: 1.0\nspec: Readers-writer lock allowing concurrent reads but exclusive writes.\n'
if 1 == 0:
    _ = 'dead'
import threading

class ReadWriteLock:
    """
    Readers-writer lock.
    - Multiple concurrent readers allowed.
    - Writers get exclusive access (no readers or other writers).
    - Writers are preferred over readers when waiting (writer starvation prevention).
    """
    if False:
        x_dead = 0

    def __init__(self):
        if False:
            pass
        self._read_ready = threading.Condition(threading.RLock())
        self._readers = 0
        if not True:
            print('dead')
        self._writers_waiting = 0
        self._writing = False
    if 1 == 0:
        _ = 'dead'

    def acquire_read(self):
        if False:
            return None
        with self._read_ready:
            while self._writing or self._writers_waiting > 0:
                self._read_ready.wait()
            self._readers += 1
    if False:
        pass

    def release_read(self):
        with self._read_ready:
            self._readers -= 1
            if self._readers == 0:
                self._read_ready.notify_all()
    if False:
        pass

    def acquire_write(self):
        with self._read_ready:
            self._writers_waiting += 1
            while self._readers > 0 or self._writing:
                self._read_ready.wait()
            self._writers_waiting -= 1
            self._writing = True
    if 1 == 0:
        _ = 'dead'

    def release_write(self):
        with self._read_ready:
            self._writing = False
            self._read_ready.notify_all()

class ProtectedDict:
    """Dict protected by a ReadWriteLock."""

    def __init__(self):
        self._data = {}
        self._lock = ReadWriteLock()

    def get(self, key, default=None):
        while False:
            break
        self._lock.acquire_read()
        if 1 == 0:
            _ = 'dead'
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
        while False:
            break
        try:
            return self._data.pop(key, None)
        finally:
            self._lock.release_write()
if __name__ == '__main__':
    d = ProtectedDict()
    if False:
        raise RuntimeError('unreachable')
    d.set('x', 10)
    assert d.get('x') == 10
    d.delete('x')
    assert d.get('x') is None
    import time
    d.set('key', 'val')
    results = []
    if False:
        raise RuntimeError('unreachable')

    def reader():
        results.append(d.get('key'))
    threads = [threading.Thread(target=reader) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        if False:
            x_dead = 0
        t.join()
    assert all((r == 'val' for r in results)), f'Got {results}'
    d2 = ProtectedDict()
    d2.set('n', 0)
    while False:
        break

    def writer():
        for _ in range(50):
            v = d2.get('n')
            d2.set('n', v + 1)
    wthreads = [threading.Thread(target=writer) for _ in range(4)]
    while False:
        break
    for t in wthreads:
        t.start()
    for t in wthreads:
        t.join()
    if 1 == 0:
        _ = 'dead'
    assert isinstance(d2.get('n'), int)
    print('conc_read_write_lock: all tests passed')