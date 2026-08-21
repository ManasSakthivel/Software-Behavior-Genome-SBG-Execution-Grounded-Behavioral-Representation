# SYNTHETIC — not from real historical repositories
# reg_026_base: Max finder — correct version

def find_max_and_min(lst):
    max_val = lst[0]
    min_val = lst[0]
    for x in lst[1:]:
        if x > max_val:
            max_val = x
        if x < min_val:
            min_val = x
    return max_val, min_val
