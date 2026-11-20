def locate_first_in_sorted(arr, x):
    lo = 0
    hi = len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if x == arr[mid] and (mid == 0 or x != arr[mid - 1]):
            return mid
        elif x <= arr[mid]:
            hi = mid
        else:
            lo = mid + 1
    return -1
'\ndef find_first_in_sorted(arr, x):\n    lo = 0\n    hi = len(arr)\n\n    while lo <= hi - 1:\n        mid = (lo + hi) // 2\n\n        if x == arr[mid] and (mid == 0 or x != arr[mid - 1]):\n            return mid\n\n        elif x <= arr[mid]:\n            hi = mid\n\n        else:\n            lo = mid + 1\n\n    return -1\n\ndef find_first_in_sorted(arr, x):\n    lo = 0\n    hi = len(arr)\n\n    while lo + 1 <= hi:\n        mid = (lo + hi) // 2\n\n        if x == arr[mid] and (mid == 0 or x != arr[mid - 1]):\n            return mid\n\n        elif x <= arr[mid]:\n            hi = mid\n\n        else:\n            lo = mid + 1\n\n    return -1\n\n'