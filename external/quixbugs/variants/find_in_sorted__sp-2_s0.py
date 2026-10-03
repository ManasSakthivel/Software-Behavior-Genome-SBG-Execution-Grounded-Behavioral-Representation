def locate_in_sorted(arr, x):

    def fn_binsearch(start, end):
        if start == end:
            return -1
        mid = start + (end - start) // 2
        if x < arr[mid]:
            return fn_binsearch(start, mid)
        elif x > arr[mid]:
            return fn_binsearch(mid + 1, end)
        else:
            return mid
    return fn_binsearch(0, len(arr))