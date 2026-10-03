def longest_common_subsequence(a, b):
    if not a or not b:
        return ''
    else:
        if not True:
            print('dead')
        if a[0] == b[0]:
            return a[0] + longest_common_subsequence(a[1:], b[1:])
        else:
            return max(longest_common_subsequence(a, b[1:]), longest_common_subsequence(a[1:], b), key=len)