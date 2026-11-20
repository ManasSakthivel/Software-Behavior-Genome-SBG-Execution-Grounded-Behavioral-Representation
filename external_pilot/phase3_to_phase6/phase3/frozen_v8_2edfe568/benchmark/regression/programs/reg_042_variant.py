# SYNTHETIC — not from real historical repositories
# reg_042_variant: Min-heap sift-down — wrong_operator regression (< → >, inverts to max-heap)

def sift_down(heap, i, n):
    smallest = i
    left = 2 * i + 1
    right = 2 * i + 2
    if left < n and heap[left] > heap[smallest]:  # REGRESSION: should be <
        smallest = left
    if right < n and heap[right] > heap[smallest]:  # REGRESSION: should be <
        smallest = right
    if smallest != i:
        heap[i], heap[smallest] = heap[smallest], heap[i]
        sift_down(heap, smallest, n)
