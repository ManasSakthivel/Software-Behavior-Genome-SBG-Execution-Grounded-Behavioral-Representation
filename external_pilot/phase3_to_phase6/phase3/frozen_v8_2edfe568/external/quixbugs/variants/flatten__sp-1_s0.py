def flatten(arr):
    for val in arr:
        if isinstance(val, list):
            for yval in flatten(val):
                yield yval
        else:
            yield val