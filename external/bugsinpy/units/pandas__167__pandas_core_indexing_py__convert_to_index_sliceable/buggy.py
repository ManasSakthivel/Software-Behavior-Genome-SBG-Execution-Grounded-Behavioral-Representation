# BugsInPy pandas/167 | https://github.com/pandas-dev/pandas | pandas/core/indexing.py | unit convert_to_index_sliceable
# license: BSD-3-Clause (upstream project); extracted verbatim, closure only, no edits
# commit 6af6d5133c3172618bb550c7aba16eabc5e362c5 (buggy)
def convert_to_index_sliceable(obj, key):
    """
    if we are index sliceable, then return my slicer, otherwise return None
    """
    idx = obj.index
    if isinstance(key, slice):
        return idx._convert_slice_indexer(key, kind="getitem")

    elif isinstance(key, str):

        # we are an actual column
        if key in obj._data.items:
            return None

        # We might have a datetimelike string that we can translate to a
        # slice here via partial string indexing
        if idx.is_all_dates:
            try:
                return idx._get_string_slice(key)
            except (KeyError, ValueError, NotImplementedError):
                return None

    return None
