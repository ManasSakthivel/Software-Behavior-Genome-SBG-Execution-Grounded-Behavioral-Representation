def get_name(obj, default='unknown'):
    if obj is None:
        return default
    return obj.name