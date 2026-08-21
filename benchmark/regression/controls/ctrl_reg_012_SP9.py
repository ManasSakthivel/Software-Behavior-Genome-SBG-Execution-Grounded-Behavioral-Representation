def pct_change(old, new):
    if old == 0:
        return None
    return (new - old) / old