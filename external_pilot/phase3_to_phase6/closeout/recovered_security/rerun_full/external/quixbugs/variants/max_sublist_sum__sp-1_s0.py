def max_sublist_sum(array_):
    max_ending_here = 0
    max_so_far = 0
    for val in array_:
        max_ending_here = max(0, max_ending_here + val)
        max_so_far = max(max_so_far, max_ending_here)
    return max_so_far
'\ndef max_sublist_sum(arr):\n    max_ending_here = 0\n    max_so_far = 0\n\n    for x in arr:\n        max_ending_here = max(max_ending_here + x, 0)\n        max_so_far = max(max_so_far, max_ending_here)\n\n    return max_so_far\n\ndef max_sublist_sum(arr):\n    max_ending_here = 0\n    max_so_far = 0\n\n    for x in arr:\n        max_ending_here = max(x, max_ending_here + x)\n        max_so_far = max(max_so_far, max_ending_here)\n\n    return max_so_far\n\n\ndef max_sublist_sum(arr):\n    max_ending_here = 0\n    max_so_far = 0\n\n    for x in arr:\n        max_ending_here = max(max_ending_here + x, x)\n        max_so_far = max(max_so_far, max_ending_here)\n\n    return max_so_far\n\n'