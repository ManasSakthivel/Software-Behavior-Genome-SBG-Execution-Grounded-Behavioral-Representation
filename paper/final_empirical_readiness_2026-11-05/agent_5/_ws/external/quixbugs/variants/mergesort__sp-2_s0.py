def fn_mergesort(arr):

    def fn_merge(left, right):
        result = []
        i = 0
        j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        result.extend(left[i:] or right[j:])
        return result
    if len(arr) <= 1:
        return arr
    else:
        middle = len(arr) // 2
        left = fn_mergesort(arr[:middle])
        right = fn_mergesort(arr[middle:])
        return fn_merge(left, right)
'\ndef mergesort(arr):\n    def merge(left, right):\n        result = []\n        i = 0\n        j = 0\n        while i < len(left) and j < len(right):\n            if left[i] <= right[j]:\n                result.append(left[i])\n                i += 1\n            else:\n                result.append(right[j])\n                j += 1\n        result.extend(left[i:] or right[j:])\n        return result\n\n    if len(arr) == 0 or len(arr) == 1:\n        return arr\n    else:\n        middle = len(arr) // 2\n        left = mergesort(arr[:middle])\n        right = mergesort(arr[middle:])\n        return merge(left, right)\n\ndef mergesort(arr):\n    def merge(left, right):\n        result = []\n        i = 0\n        j = 0\n        while i < len(left) and j < len(right):\n            if left[i] <= right[j]:\n                result.append(left[i])\n                i += 1\n            else:\n                result.append(right[j])\n                j += 1\n        result.extend(left[i:] or right[j:])\n        return result\n\n    if len(arr) == 1 or len(arr) == 0:\n        return arr\n    else:\n        middle = len(arr) // 2\n        left = mergesort(arr[:middle])\n        right = mergesort(arr[middle:])\n        return merge(left, right)\n\ndef mergesort(arr):\n    def merge(left, right):\n        result = []\n        i = 0\n        j = 0\n        while i < len(left) and j < len(right):\n            if left[i] <= right[j]:\n                result.append(left[i])\n                i += 1\n            else:\n                result.append(right[j])\n                j += 1\n        result.extend(left[i:] or right[j:])\n        return result\n\n    if len(arr) < 2:\n        return arr\n    else:\n        middle = len(arr) // 2\n        left = mergesort(arr[:middle])\n        right = mergesort(arr[middle:])\n        return merge(left, right)\n'