"""
program_id: conc_producer_consumer
category: Concurrency Simulation
spec_version: 1.0
spec: Bounded producer-consumer queue with blocking put/get and sentinel shutdown.
"""
import threading
import queue
from typing import Callable, List
SENTINEL = object()

def run_pipeline(producer_fn: Callable, consumer_fn: Callable, n_producers=2, n_consumers=2, buffer_size=10) -> List:
    """
    producer_fn() -> yields items or returns list
    consumer_fn(item) -> processed item (or None to drop)
    Returns list of all non-None consumer results, in arrival order.
    """
    q: queue.Queue = queue.Queue(maxsize=buffer_size)
    results = []
    results_lock = threading.Lock()

    def producer_worker():
        try:
            for item in producer_fn():
                q.put(item)
        finally:
            q.put(SENTINEL)

    def consumer_worker():
        while True:
            item = q.get()
            if item is SENTINEL:
                q.put(SENTINEL)
                break
            out = consumer_fn(item)
            if out is not None:
                with results_lock:
                    results.append(out)
    producers = [threading.Thread(target=producer_worker) for _ in range(n_producers)]
    consumers = [threading.Thread(target=consumer_worker) for _ in range(n_consumers)]
    for t in consumers:
        t.start()
    for t in producers:
        t.start()
    for t in producers:
        t.join()
    for t in consumers:
        t.join()
    return results
if __name__ == '__main__':
    items = list(range(20))
    idx = [0]
    lock = threading.Lock()

    def prod():
        for x in range(20):
            yield x
    results = run_pipeline(prod, lambda x: x * 2, n_producers=1, n_consumers=2, buffer_size=5)
    assert sorted(results) == [x * 2 for x in range(20)], f'Got {sorted(results)}'
    results2 = run_pipeline(prod, lambda x: x if x % 2 == 0 else None, n_producers=1, n_consumers=1, buffer_size=4)
    assert sorted(results2) == list(range(0, 20, 2))
    results3 = run_pipeline(lambda : [], lambda x: x, n_producers=1, n_consumers=1, buffer_size=2)
    assert results3 == []
    print('conc_producer_consumer: all tests passed')
