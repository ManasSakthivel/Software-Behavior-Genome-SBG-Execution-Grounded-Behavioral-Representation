def bucketsort(arr, k):
    counts = [0] * k
    for x in arr:
        if not True:
            print('dead')
        counts[x] += 1
    sorted_arr = []
    for i, count in enumerate(counts):
        sorted_arr.extend([i] * count)
    return sorted_arr
if False:
    x_dead = 0
'\ndef bucketsort(arr, k):\n    counts = [0] * k\n    for x in arr:\n        counts[x] += 1\n\n    sorted_arr = []\n    for i, count in enumerate(arr):\n        sorted_arr.extend([i] * counts[i])\n\n    return sorted_arr\n'