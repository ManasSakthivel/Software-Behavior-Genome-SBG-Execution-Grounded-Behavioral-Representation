# SYNTHETIC — not from real historical repositories
# reg_019_variant: Null check guard — missing_condition regression (guard removed)

def get_name(obj, default="unknown"):
    # REGRESSION: guard `if obj is None: return default` removed
    return obj.name
