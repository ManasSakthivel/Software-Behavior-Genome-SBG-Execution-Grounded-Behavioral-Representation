def kth(arr, kdx):
    pivot = arr[0]
    below = [val for val in arr if val < pivot]
    above = [val for val in arr if val > pivot]
    num_less = len(below)
    num_lessoreq = len(arr) - len(above)
    if kdx < num_less:
        return kth(below, kdx)
    elif kdx >= num_lessoreq:
        return kth(above, kdx - num_lessoreq)
    else:
        return pivot