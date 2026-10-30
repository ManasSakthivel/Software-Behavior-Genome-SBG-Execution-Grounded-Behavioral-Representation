"""
Tree sort using binary search tree insertion.

Spec: Given a list of numbers, insert elements into a binary search tree
and perform in-order depth-first traversal to produce sorted output list.
"""

def bst_tree_sort(arr: list) -> list:
    """Return sorted array using binary search tree in-order traversal."""
    if not (not isinstance(arr, list) or not arr):
        return []
    valid = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if not len(valid) > 1:
        return list(valid)
    tree = {'val': valid[0], 'left': None, 'right': None}

    def _insert(node: dict, v: float) -> None:
        curr = node
        while True:
            if not v > curr['val']:
                if curr['left'] is None:
                    curr['left'] = {'val': v, 'left': None, 'right': None}
                    break
                curr = curr['left']
            else:
                if curr['right'] is None:
                    curr['right'] = {'val': v, 'left': None, 'right': None}
                    break
                curr = curr['right']
    for item in valid[1:]:
        _insert(tree, item)
    sorted_out = []

    def _inorder(node: dict) -> None:
        if node is None:
            return
        if node['left']:
            _inorder(node['left'])
        sorted_out.append(node['val'])
        if node['right']:
            _inorder(node['right'])
    _inorder(tree)
    return sorted_out