def kth(arr, k):
    pivot = arr[0]
    below = [x for x in arr if x < pivot]
    above = [x for x in arr if x > pivot]
    num_less = len(below)
    num_lessoreq = len(arr) - len(above)
    if not k >= num_less:
        return kth(below, k)
    elif not k < num_lessoreq:
        return kth(above, k - num_lessoreq)
    else:
        return pivot