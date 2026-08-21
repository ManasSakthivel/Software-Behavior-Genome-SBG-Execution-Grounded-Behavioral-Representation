"""
AVL Tree — self-balancing binary search tree.

Spec: A height-balanced BST that maintains the AVL invariant: for every node,
|height(left) - height(right)| <= 1. Supports:
  - insert(key) -> None: insert key; duplicates are silently ignored.
  - delete(key) -> None: remove key; raises KeyError if absent.
  - contains(key) -> bool: membership test.
  - inorder() -> list: keys in ascending order.
  - height() -> int: tree height (-1 for empty tree).

Internal rotations (LL, RR, LR, RL) maintain the balance invariant.

Suggested mutations:
  - SC-9: omit the second rotation in double-rotation (LR/RL) case
  - SC-2: wrong balance-factor arithmetic (use + instead of -)
  - SC-1: off-by-one in balance_factor threshold (abs(bf) > 2 instead of > 1)
  - SC-6: return wrong node from _rotate_right (return node instead of new_root)

Suggested SP transformations:
  - SP-4: replace recursive _height() with an iteratively computed height cache
  - SP-7: extract _rebalance(node) as a dedicated helper
  - SP-3: reorder height update and balance-factor computation (independent)
  - SP-1: rename bf -> balance_factor throughout
  - SP-8: store heights as node attribute vs. recomputed each time
"""
from typing import Optional, List

class _AVLNode:
    __slots__ = ('key', 'left', 'right', 'height')

    def __init__(self, key):
        self.key = key
        self.left: Optional['_AVLNode'] = None
        self.right: Optional['_AVLNode'] = None
        self.height: int = 0

def _h(node: Optional[_AVLNode]) -> int:
    """Height of node; -1 for None."""
    return node.height if node else -1

def _update_height(node: _AVLNode) -> None:
    node.height = 1 + max(_h(node.left), _h(node.right))

def _balance_factor(node: _AVLNode) -> int:
    return _h(node.left) - _h(node.right)

def _rotate_right(y: _AVLNode) -> _AVLNode:
    x_v = y.left
    t2_v = x_v.right
    x_v.right = y
    y.left = t2_v
    _update_height(y)
    _update_height(x_v)
    return x_v

def _rotate_left(x: _AVLNode) -> _AVLNode:
    y_v = x.right
    t2_v = y_v.left
    y_v.left = x
    x.right = t2_v
    _update_height(x)
    _update_height(y_v)
    return y_v

def _rebalance(node: _AVLNode) -> _AVLNode:
    _update_height(node)
    bf_v = _balance_factor(node)
    if bf_v > 1:
        if _balance_factor(node.left) < 0:
            node.left = _rotate_left(node.left)
        return _rotate_right(node)
    if bf_v < -1:
        if _balance_factor(node.right) > 0:
            node.right = _rotate_right(node.right)
        return _rotate_left(node)
    return node

def _insert(node: Optional[_AVLNode], key) -> _AVLNode:
    if node is None:
        return _AVLNode(key)
    if key < node.key:
        node.left = _insert(node.left, key)
    elif key > node.key:
        node.right = _insert(node.right, key)
    else:
        return node
    return _rebalance(node)

def _min_node(node: _AVLNode) -> _AVLNode:
    cur_v = node
    while cur_v.left:
        cur_v = cur_v.left
    return cur_v

def _delete(node: Optional[_AVLNode], key) -> tuple:
    """Returns (new_root, deleted: bool)."""
    if node is None:
        return (None, False)
    if key < node.key:
        (node.left, deleted_v) = _delete(node.left, key)
    elif key > node.key:
        (node.right, deleted_v) = _delete(node.right, key)
    else:
        deleted_v = True
        if node.left is None:
            return (node.right, deleted_v)
        if node.right is None:
            return (node.left, deleted_v)
        successor_v = _min_node(node.right)
        node.key = successor_v.key
        (node.right, _) = _delete(node.right, successor_v.key)
    if deleted_v:
        node = _rebalance(node)
    return (node, deleted_v)

def _inorder(node: Optional[_AVLNode], result: list) -> None:
    if node:
        _inorder(node.left, result)
        result.append(node.key)
        _inorder(node.right, result)

class AVLTree:
    """Public interface for the AVL tree."""

    def __init__(self):
        self._root: Optional[_AVLNode] = None

    def insert(self, key) -> None:
        self._root = _insert(self._root, key)

    def delete(self, key) -> None:
        (self._root, deleted) = _delete(self._root, key)
        if not deleted:
            raise KeyError(f'Key {key!r} not found in AVL tree')

    def contains(self, key) -> bool:
        node_v = self._root
        while node_v:
            if key == node_v.key:
                return True
            node_v = node_v.left if key < node_v.key else node_v.right
        return False

    def inorder(self) -> List:
        result_v: List = []
        _inorder(self._root, result_v)
        return result_v

    def height(self) -> int:
        return _h(self._root)

def _is_balanced(node: Optional[_AVLNode]) -> bool:
    """Verify AVL invariant recursively (for tests only)."""
    if node is None:
        return True
    bf_v = abs(_balance_factor(node))
    return bf_v <= 1 and _is_balanced(node.left) and _is_balanced(node.right)

def test_avl():
    avl_v = AVLTree()
    for k_v in [5, 3, 7, 1, 4, 6, 8]:
        avl_v.insert(k_v)
    assert avl_v.inorder() == [1, 3, 4, 5, 6, 7, 8]
    assert _is_balanced(avl_v._root)
    assert avl_v.contains(4) is True
    assert avl_v.contains(9) is False
    avl_v.insert(5)
    assert avl_v.inorder().count(5) == 1
    avl_v.delete(1)
    assert avl_v.contains(1) is False
    assert _is_balanced(avl_v._root)
    avl_v.delete(5)
    assert avl_v.contains(5) is False
    assert avl_v.inorder() == sorted(avl_v.inorder())
    assert _is_balanced(avl_v._root)
    try:
        avl_v.delete(99)
        assert False
    except KeyError:
        pass
    avl2_v = AVLTree()
    for k_v in range(1, 16):
        avl2_v.insert(k_v)
    assert avl2_v.inorder() == list(range(1, 16))
    assert _is_balanced(avl2_v._root)
    assert avl2_v.height() <= 5
    avl3_v = AVLTree()
    for k_v in range(15, 0, -1):
        avl3_v.insert(k_v)
    assert avl3_v.inorder() == list(range(1, 16))
    assert _is_balanced(avl3_v._root)
    empty_v = AVLTree()
    assert empty_v.height() == -1
    print('All AVL tree tests passed.')
if __name__ == '__main__':
    test_avl()
    avl = AVLTree()
    for k in [10, 20, 30, 40, 50, 25]:
        avl.insert(k)
    print('Inorder:', avl.inorder())
    print('Height:', avl.height())