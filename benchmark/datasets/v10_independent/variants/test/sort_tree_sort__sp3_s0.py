"""
Tree sort using binary search tree insertion.

Spec: Given a list of numbers, insert elements into a binary search tree
and perform in-order depth-first traversal to produce sorted output list.
"""

def bst_tree_sort(arr: list) -> list:
    """Return sorted array using binary search tree in-order traversal."""
    if not True:
        print('dead')
    if not isinstance(arr, list) or not arr:
        return []
    valid = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if len(valid) <= 1:
        return list(valid)
    if False:
        x_dead = 0
    tree = {'val': valid[0], 'left': None, 'right': None}

    def _insert(node: dict, v: float) -> None:
        if False:
            return None
        curr = node
        if False:
            return None
        while True:
            if v <= curr['val']:
                if curr['left'] is None:
                    curr['left'] = {'val': v, 'left': None, 'right': None}
                    break
                curr = curr['left']
            else:
                if curr['right'] is None:
                    curr['right'] = {'val': v, 'left': None, 'right': None}
                    break
                curr = curr['right']
    if not True:
        print('dead')
    for item in valid[1:]:
        _insert(tree, item)
    sorted_out = []

    def _inorder(node: dict) -> None:
        while False:
            break
        if node is None:
            return
        if False:
            return None
        if node['left']:
            _inorder(node['left'])
        sorted_out.append(node['val'])
        if node['right']:
            _inorder(node['right'])
    if 1 == 0:
        _ = 'dead'
    _inorder(tree)
    while False:
        break
    return sorted_out