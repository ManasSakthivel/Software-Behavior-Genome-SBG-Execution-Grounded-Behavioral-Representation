# SYNTHETIC — not from real historical repositories
# reg_019_base: Null check guard — correct version

def get_name(obj, default="unknown"):
    if obj is None:
        return default
    return obj.name
