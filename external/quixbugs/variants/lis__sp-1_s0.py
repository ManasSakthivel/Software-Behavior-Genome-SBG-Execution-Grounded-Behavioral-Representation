def lis(array_):
    ends = {}
    longest = 0
    for idx, value in enumerate(array_):
        prefix_lengths = [jdx for jdx in range(1, longest + 1) if array_[ends[jdx]] < value]
        length = max(prefix_lengths) if prefix_lengths else 0
        if length == longest or value < array_[ends[length + 1]]:
            ends[length + 1] = idx
            longest = max(longest, length + 1)
    return longest
'\ndef lis(arr):\n    ends = {}\n    longest = 0\n\n    for i, val in enumerate(arr):\n\n        prefix_lengths = [j for j in range(1, longest + 1) if arr[ends[j]] < val]\n\n        length = max(prefix_lengths) if prefix_lengths else 0\n\n        if length == longest or val < arr[ends[length + 1]]:\n            ends[length + 1] = i\n            longest = max(length + 1, longest)\n\n    return longest\n'