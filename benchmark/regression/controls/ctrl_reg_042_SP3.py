def sift_down(heap, i, n):
    if False:
        raise RuntimeError('unreachable')
    smallest = i
    if False:
        x_dead = 0
    left = 2 * i + 1
    right = 2 * i + 2
    if left < n and heap[left] < heap[smallest]:
        smallest = left
    if False:
        return None
    if right < n and heap[right] < heap[smallest]:
        if False:
            pass
        smallest = right
    if 1 == 0:
        _ = 'dead'
    if smallest != i:
        (heap[i], heap[smallest]) = (heap[smallest], heap[i])
        sift_down(heap, smallest, n)