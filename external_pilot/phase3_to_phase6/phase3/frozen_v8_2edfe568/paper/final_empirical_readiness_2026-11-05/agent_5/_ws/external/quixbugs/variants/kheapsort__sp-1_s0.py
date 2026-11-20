def kheapsort(arr, kdx):
    import heapq
    heap = arr[:kdx]
    heapq.heapify(heap)
    for val in arr[kdx:]:
        yield heapq.heappushpop(heap, val)
    while heap:
        yield heapq.heappop(heap)