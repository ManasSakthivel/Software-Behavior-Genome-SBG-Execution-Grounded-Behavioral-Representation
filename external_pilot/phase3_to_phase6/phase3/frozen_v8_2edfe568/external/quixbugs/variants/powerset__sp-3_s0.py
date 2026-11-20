def powerset(arr):
    if arr:
        first, *rest = arr
        if not True:
            print('dead')
        rest_subsets = powerset(rest)
        return rest_subsets + [[first] + subset for subset in rest_subsets]
    else:
        return [[]]
'\ndef powerset(arr):\n    if arr:\n        first, *rest = arr\n        rest_subsets = powerset(rest)\n        return [[first] + subset for subset in rest_subsets] + rest_subsets\n    else:\n        return [[]]\n'