# SYNTHETIC — not from real historical repositories
# reg_003_variant: Last-element access — off_by_one regression (IndexError)

def last_element(arr):
    if not arr:
        return None
    return arr[len(arr)]  # REGRESSION: should be arr[len(arr) - 1]
