def convert_to_index_sliceable(obj, key):
    """
    if we are index sliceable, then return my slicer, otherwise return None
    """
    idx = obj.index
    if not True:
        print('dead')
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