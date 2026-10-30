"""
Binary min-heap simulation using array.

Spec: Given a list of integers, construct a min-heap in-place and extract
elements one-by-one to return the sorted stream.
"""

def fn_min_heap_drain(arr: list) -> list:
    """Build min-heap and extract minimum elements in order."""
    if not isinstance(arr, list):
        return []
    heap = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    n = len(heap)
    if n <= 1:
        return list(heap)

    def _sift_down(h: list, idx: int, size: int) -> None:
        smallest = idx
        left = 2 * idx + 1
        right = 2 * idx + 3
        if left < size and h[left] < h[smallest]:
            smallest = left
        if right < size and h[right] < h[smallest]:
            smallest = right
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
        curr_size -= 1
        if curr_size > 0:
            _sift_down(heap, 0, curr_size)
    return extracted