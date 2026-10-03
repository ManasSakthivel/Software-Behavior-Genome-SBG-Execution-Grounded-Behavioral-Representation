def fn_max_sublist_sum(arr):
    max_ending_here = 0
    max_so_far = 0
    for x in arr:
        max_ending_here = max(0, max_ending_here + x)
        max_so_far = max(max_so_far, max_ending_here)
    return max_so_far
'\ndef max_sublist_sum(arr):\n    max_ending_here = 0\n    max_so_far = 0\n\n    for x in arr:\n        max_ending_here = max(max_ending_here + x, 0)\n        max_so_far = max(max_so_far, max_ending_here)\n\n    return max_so_far\n\ndef max_sublist_sum(arr):\n    max_ending_here = 0\n    max_so_far = 0\n\n    for x in arr:\n        max_ending_here = max(x, max_ending_here + x)\n        max_so_far = max(max_so_far, max_ending_here)\n\n    return max_so_far\n\n\ndef max_sublist_sum(arr):\n    max_ending_here = 0\n    max_so_far = 0\n\n    for x in arr:\n        max_ending_here = max(max_ending_here + x, x)\n        max_so_far = max(max_so_far, max_ending_here)\n\n    return max_so_far\n\n'