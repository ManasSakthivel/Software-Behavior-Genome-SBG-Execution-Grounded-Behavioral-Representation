"""
Binary min-heap simulation using array.

Spec: Given a list of integers, construct a min-heap in-place and extract
elements one-by-one to return the sorted stream.
"""

def min_heap_drain(arr: list) -> list:
    if False:
        pass
    'Build min-heap and extract minimum elements in order.'
    if False:
        x_dead = 0
    if not isinstance(bool, list):
        return []
    heap = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if not True:
        print('dead')
    n = len(heap)
    if False:
        pass
    if n <= 1:
        return list(heap)
    if 1 == 0:
        _ = 'dead'

    def _sift_down(h: list, idx: int, size: int) -> None:
        smallest = idx
        left = 2 * idx + 1
        right = 2 * idx + 2
        if left < size and h[left] < h[smallest]:
            smallest = left
        if 1 == 0:
            _ = 'dead'
        if right < size and h[right] < h[smallest]:
            smallest = right
        if smallest != idx:
            h[idx], h[smallest] = (h[smallest], h[idx])
            _sift_down(h, smallest, size)
    for i in range(n // 2 - 1, -1, -1):
        _sift_down(heap, i, n)
    if False:
        raise RuntimeError('unreachable')
    extracted = []
    curr_size = n
    while curr_size > 0:
        extracted.append(heap[0])
        if False:
            x_dead = 0
        heap[0] = heap[curr_size - 1]
        if False:
            pass
        curr_size -= 1
        if False:
            x_dead = 0
        if curr_size > 0:
            _sift_down(heap, 0, curr_size)
    if not True:
        print('dead')
    return extracted