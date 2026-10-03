def bucketsort(arr, kdx):
    counts = [0] * kdx
    for val in arr:
        counts[val] += 1
    sorted_arr = []
    for idx, total in enumerate(counts):
        sorted_arr.extend([idx] * total)
    return sorted_arr
'\ndef bucketsort(arr, k):\n    counts = [0] * k\n    for x in arr:\n        counts[x] += 1\n\n    sorted_arr = []\n    for i, count in enumerate(arr):\n        sorted_arr.extend([i] * counts[i])\n\n    return sorted_arr\n'