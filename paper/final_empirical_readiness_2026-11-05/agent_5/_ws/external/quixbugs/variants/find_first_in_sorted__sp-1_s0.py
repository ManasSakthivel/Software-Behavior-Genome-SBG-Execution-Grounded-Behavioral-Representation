def find_first_in_sorted(array_, val):
    lo = 0
    hi = len(array_)
    while lo < hi:
        mid = (lo + hi) // 2
        if val == array_[mid] and (mid == 0 or val != array_[mid - 1]):
            return mid
        elif val <= array_[mid]:
            hi = mid
        else:
            lo = mid + 1
    return -1
'\ndef find_first_in_sorted(arr, x):\n    lo = 0\n    hi = len(arr)\n\n    while lo <= hi - 1:\n        mid = (lo + hi) // 2\n\n        if x == arr[mid] and (mid == 0 or x != arr[mid - 1]):\n            return mid\n\n        elif x <= arr[mid]:\n            hi = mid\n\n        else:\n            lo = mid + 1\n\n    return -1\n\ndef find_first_in_sorted(arr, x):\n    lo = 0\n    hi = len(arr)\n\n    while lo + 1 <= hi:\n        mid = (lo + hi) // 2\n\n        if x == arr[mid] and (mid == 0 or x != arr[mid - 1]):\n            return mid\n\n        elif x <= arr[mid]:\n            hi = mid\n\n        else:\n            lo = mid + 1\n\n    return -1\n\n'