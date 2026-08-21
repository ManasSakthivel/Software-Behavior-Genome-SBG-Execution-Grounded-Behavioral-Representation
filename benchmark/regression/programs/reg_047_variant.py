# SYNTHETIC — not from real historical repositories
# reg_047_variant: Score normalisation — missing_condition regression (ZeroDivisionError for uniform input)

def normalise(values):
    if not values:
        return []
    min_val = min(values)
    max_val = max(values)
    # REGRESSION: `if max_val == min_val: return [0.0] * len(values)` guard removed
    return [(v - min_val) / (max_val - min_val) for v in values]
