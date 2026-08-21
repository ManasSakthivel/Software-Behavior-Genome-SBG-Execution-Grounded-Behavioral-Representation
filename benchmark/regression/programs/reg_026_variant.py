# SYNTHETIC — not from real historical repositories
# reg_026_variant: Max finder — wrong_return regression (returns min_val instead of max_val first)

def find_max_and_min(lst):
    max_val = lst[0]
    min_val = lst[0]
    for x in lst[1:]:
        if x > max_val:
            max_val = x
        if x < min_val:
            min_val = x
    return min_val, min_val  # REGRESSION: should be return max_val, min_val
