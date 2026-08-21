# SYNTHETIC — not from real historical repositories
# reg_022_variant: Dedup insert — missing_condition regression (guard removed)

def unique_append(seen, result, item):
    # REGRESSION: `if item not in seen:` guard removed — duplicates silently added
    seen.add(item)
    result.append(item)
    return result
