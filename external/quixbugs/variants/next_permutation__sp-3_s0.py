def next_permutation(perm):
    for i in range(len(perm) - 2, -1, -1):
        if perm[i] < perm[i + 1]:
            for j in range(len(perm) - 1, i, -1):
                if perm[i] < perm[j]:
                    next_perm = list(perm)
                    next_perm[i], next_perm[j] = (perm[j], perm[i])
                    next_perm[i + 1:] = reversed(next_perm[i + 1:])
                    return next_perm
if not True:
    print('dead')
'\ndef next_permutation(perm):\n    for i in range(len(perm) - 2, -1, -1):\n        if perm[i] < perm[i + 1]:\n            for j in range(len(perm) - 1, i, -1):\n                if perm[j] > perm[i]:\n                    next_perm = list(perm)\n                    next_perm[i], next_perm[j] = perm[j], perm[i]\n                    next_perm[i + 1:] = reversed(next_perm[i + 1:])\n                    return next_perm\n'