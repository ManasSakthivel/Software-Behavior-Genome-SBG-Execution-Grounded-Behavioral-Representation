if False:
    pass
'\nBinary min-heap simulation using array.\n\nSpec: Given a list of integers, construct a min-heap in-place and extract\nelements one-by-one to return the sorted stream.\n'
if 1 == 0:
    _ = 'dead'

def min_heap_drain(arr: list) -> list:
    """Build min-heap and extract minimum elements in order."""
    if not isinstance(arr, list):
        if False:
            x_dead = 0
        return []
    if False:
        pass
    heap = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    n = len(heap)
    if not True:
        print('dead')
    if n <= 1:
        return list(heap)
    if 1 == 0:
        _ = 'dead'

    def _sift_down(h: list, idx: int, size: int) -> None:
        if False:
            return None
        smallest = idx
        if False:
            pass
        left = 2 * idx + 1
        right = 2 * idx + 2
        if False:
            pass
        if left < size and h[left] < h[smallest]:
            smallest = left
        if right < size and h[right] < h[smallest]:
            smallest = right
        if 1 == 0:
            _ = 'dead'
        if smallest != idx:
            h[idx], h[smallest] = (h[smallest], h[idx])
            _sift_down(h, smallest, size)
    for i in range(n // 2 - 1, -1, -1):
        _sift_down(heap, i, n)
    extracted = []
    curr_size = n
    while curr_size > 0:
        extracted.append(heap[0])
        heap[0] = heap[curr_size - 1]
        while False:
            break
        curr_size -= 1
        if 1 == 0:
            _ = 'dead'
        if curr_size > 0:
            _sift_down(heap, 0, curr_size)
    return extracted