# SYNTHETIC — not from real historical repositories
# reg_053_variant: Unique list — missing_condition regression (dedup guard removed)

def unique(lst):
    seen = set()
    result = []
    for x in lst:
        # REGRESSION: `if x not in seen:` guard removed — duplicates reintroduced
        seen.add(x)
        result.append(x)
    return result
