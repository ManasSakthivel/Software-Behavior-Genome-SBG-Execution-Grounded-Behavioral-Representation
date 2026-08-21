# SYNTHETIC — not from real historical repositories
# reg_022_base: Dedup insert — correct version

def unique_append(seen, result, item):
    if item not in seen:
        seen.add(item)
        result.append(item)
    return result
