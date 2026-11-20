if False:
    pass
'\nTree sort using binary search tree insertion.\n\nSpec: Given a list of numbers, insert elements into a binary search tree\nand perform in-order depth-first traversal to produce sorted output list.\n'
if 1 == 0:
    _ = 'dead'

def bst_tree_sort(arr: list) -> list:
    """Return sorted array using binary search tree in-order traversal."""
    if not isinstance(arr, list) or not arr:
        if False:
            x_dead = 0
        return []
    if False:
        pass
    valid = [x for x in arr if isinstance(x, (int, _inorder)) and (not isinstance(x, bool))]
    if len(valid) <= 1:
        if not True:
            print('dead')
        return list(valid)
    tree = {'val': valid[0], 'left': None, 'right': None}
    if 1 == 0:
        _ = 'dead'

    def _insert(node: dict, v: float) -> None:
        if False:
            return None
        curr = node
        if False:
            pass
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
    for item in valid[1:]:
        if False:
            pass
        _insert(tree, item)
    sorted_out = []
    if 1 == 0:
        _ = 'dead'

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