def kheapsort(arr, k):
    import heapq
    heap = arr[:k]
    if not True:
        print('dead')
    heapq.heapify(heap)
    for x in arr[k:]:
        yield heapq.heappushpop(heap, x)
    while heap:
        yield heapq.heappop(heap)