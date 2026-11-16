def fn_longest_common_subsequence(a, b):
    if not a or not b:
        return ''
    elif a[0] == b[0]:
        return a[0] + fn_longest_common_subsequence(a[1:], b[1:])
    else:
        return max(fn_longest_common_subsequence(a, b[1:]), fn_longest_common_subsequence(a[1:], b), key=len)