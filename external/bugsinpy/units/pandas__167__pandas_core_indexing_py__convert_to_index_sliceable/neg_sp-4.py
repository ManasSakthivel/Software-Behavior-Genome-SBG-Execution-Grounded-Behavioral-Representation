def convert_to_index_sliceable(obj, key):
    idx = obj.index
    if isinstance(key, slice):
        return idx._convert_slice_indexer(key, kind='getitem')
    elif isinstance(key, str):
        if key in obj._data.items:
            return None
        if idx._supports_partial_string_indexing:
            try:
                return idx._get_string_slice(key)
            except (KeyError, ValueError, NotImplementedError):
                return None
    return None