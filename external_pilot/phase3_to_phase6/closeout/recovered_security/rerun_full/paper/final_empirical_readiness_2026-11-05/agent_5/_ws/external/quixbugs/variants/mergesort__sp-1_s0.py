def mergesort(array_):

    def merge(left, right):
        output = []
        idx = 0
        jdx = 0
        while idx < len(left) and jdx < len(right):
            if left[idx] <= right[jdx]:
                output.append(left[idx])
                idx += 1
            else:
                output.append(right[jdx])
                jdx += 1
        output.extend(left[idx:] or right[jdx:])
        return output
    if len(array_) <= 1:
        return array_
    else:
        middle = len(array_) // 2
        left = mergesort(array_[:middle])
        right = mergesort(array_[middle:])
        return merge(left, right)
'\ndef mergesort(arr):\n    def merge(left, right):\n        result = []\n        i = 0\n        j = 0\n        while i < len(left) and j < len(right):\n            if left[i] <= right[j]:\n                result.append(left[i])\n                i += 1\n            else:\n                result.append(right[j])\n                j += 1\n        result.extend(left[i:] or right[j:])\n        return result\n\n    if len(arr) == 0 or len(arr) == 1:\n        return arr\n    else:\n        middle = len(arr) // 2\n        left = mergesort(arr[:middle])\n        right = mergesort(arr[middle:])\n        return merge(left, right)\n\ndef mergesort(arr):\n    def merge(left, right):\n        result = []\n        i = 0\n        j = 0\n        while i < len(left) and j < len(right):\n            if left[i] <= right[j]:\n                result.append(left[i])\n                i += 1\n            else:\n                result.append(right[j])\n                j += 1\n        result.extend(left[i:] or right[j:])\n        return result\n\n    if len(arr) == 1 or len(arr) == 0:\n        return arr\n    else:\n        middle = len(arr) // 2\n        left = mergesort(arr[:middle])\n        right = mergesort(arr[middle:])\n        return merge(left, right)\n\ndef mergesort(arr):\n    def merge(left, right):\n        result = []\n        i = 0\n        j = 0\n        while i < len(left) and j < len(right):\n            if left[i] <= right[j]:\n                result.append(left[i])\n                i += 1\n            else:\n                result.append(right[j])\n                j += 1\n        result.extend(left[i:] or right[j:])\n        return result\n\n    if len(arr) < 2:\n        return arr\n    else:\n        middle = len(arr) // 2\n        left = mergesort(arr[:middle])\n        right = mergesort(arr[middle:])\n        return merge(left, right)\n'