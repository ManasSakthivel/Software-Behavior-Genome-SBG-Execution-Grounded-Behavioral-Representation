# SYNTHETIC — not from real historical repositories
# reg_003_base: Last-element access — correct version

def last_element(arr):
    if not arr:
        return None
    return arr[len(arr) - 1]
