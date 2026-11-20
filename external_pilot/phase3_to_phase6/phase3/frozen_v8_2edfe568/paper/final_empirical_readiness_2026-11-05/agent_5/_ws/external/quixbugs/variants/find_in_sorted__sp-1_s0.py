def find_in_sorted(array_, val):

    def binsearch(start, end):
        if start == end:
            return -1
        mid = start + (end - start) // 2
        if val < array_[mid]:
            return binsearch(start, mid)
        elif val > array_[mid]:
            return binsearch(mid + 1, end)
        else:
            return mid
    return binsearch(0, len(array_))