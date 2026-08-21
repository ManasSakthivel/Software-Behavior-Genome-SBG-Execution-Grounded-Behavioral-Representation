# SYNTHETIC — not from real historical repositories
# reg_053_base: Unique list — correct version

def unique(lst):
    seen = set()
    result = []
    for x in lst:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result
