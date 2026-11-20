def fn_flatten(arr):
    for x in arr:
        if isinstance(x, list):
            for y in fn_flatten(x):
                yield y
        else:
            yield x