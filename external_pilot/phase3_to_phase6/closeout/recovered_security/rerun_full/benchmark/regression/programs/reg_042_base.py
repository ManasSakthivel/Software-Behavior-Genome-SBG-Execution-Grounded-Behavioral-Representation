# SYNTHETIC — not from real historical repositories
# reg_042_base: Min-heap sift-down — correct version

def sift_down(heap, i, n):
    smallest = i
    left = 2 * i + 1
    right = 2 * i + 2
    if left < n and heap[left] < heap[smallest]:
        smallest = left
    if right < n and heap[right] < heap[smallest]:
        smallest = right
    if smallest != i:
        heap[i], heap[smallest] = heap[smallest], heap[i]
        sift_down(heap, smallest, n)
