# program_id: algo_avl_tree
# category: data_structures
# spec_version: 1.0

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
    __slots__ = ("key", "left", "right", "height")

    def __init__(self, key):
        self.key = key
        self.left: Optional["_AVLNode"] = None
        self.right: Optional["_AVLNode"] = None
        self.height: int = 0


def _h(node: Optional[_AVLNode]) -> int:
    """Height of node; -1 for None."""
    return node.height if node else -1


def _update_height(node: _AVLNode) -> None:
    node.height = 1 + max(_h(node.left), _h(node.right))


def _balance_factor(node: _AVLNode) -> int:
    return _h(node.left) - _h(node.right)


def _rotate_right(y: _AVLNode) -> _AVLNode:
    x = y.left
    t2 = x.right
    x.right = y
    y.left = t2
    _update_height(y)
    _update_height(x)
    return x


def _rotate_left(x: _AVLNode) -> _AVLNode:
    y = x.right
    t2 = y.left
    y.left = x
    x.right = t2
    _update_height(x)
    _update_height(y)
    return y


def _rebalance(node: _AVLNode) -> _AVLNode:
    _update_height(node)
    bf = _balance_factor(node)
    # Left-heavy
    if bf > 1:
        if _balance_factor(node.left) < 0:     # LR case
            node.left = _rotate_left(node.left)
        return _rotate_right(node)
    # Right-heavy
    if bf < -1:
        if _balance_factor(node.right) > 0:    # RL case
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
        return node   # duplicate; no-op
    return _rebalance(node)


def _min_node(node: _AVLNode) -> _AVLNode:
    cur = node
    while cur.left:
        cur = cur.left
    return cur


def _delete(node: Optional[_AVLNode], key) -> tuple:
    """Returns (new_root, deleted: bool)."""
    if node is None:
        return None, False
    if key < node.key:
        node.left, deleted = _delete(node.left, key)
    elif key > node.key:
        node.right, deleted = _delete(node.right, key)
    else:
        deleted = True
        if node.left is None:
            return node.right, deleted
        if node.right is None:
            return node.left, deleted
        successor = _min_node(node.right)
        node.key = successor.key
        node.right, _ = _delete(node.right, successor.key)
    if deleted:
        node = _rebalance(node)
    return node, deleted


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
        self._root, deleted = _delete(self._root, key)
        if not deleted:
            raise KeyError(f"Key {key!r} not found in AVL tree")

    def contains(self, key) -> bool:
        node = self._root
        while node:
            if key == node.key:
                return True
            node = node.left if key < node.key else node.right
        return False

    def inorder(self) -> List:
        result: List = []
        _inorder(self._root, result)
        return result

    def height(self) -> int:
        return _h(self._root)


def _is_balanced(node: Optional[_AVLNode]) -> bool:
    """Verify AVL invariant recursively (for tests only)."""
    if node is None:
        return True
    bf = abs(_balance_factor(node))
    return bf <= 1 and _is_balanced(node.left) and _is_balanced(node.right)


# ---------- tests ----------

def test_avl():
    avl = AVLTree()

    # Test 1: insert + inorder
    for k in [5, 3, 7, 1, 4, 6, 8]:
        avl.insert(k)
    assert avl.inorder() == [1, 3, 4, 5, 6, 7, 8]

    # Test 2: AVL invariant after bulk insert
    assert _is_balanced(avl._root)

    # Test 3: contains
    assert avl.contains(4) is True
    assert avl.contains(9) is False

    # Test 4: duplicate insert is no-op
    avl.insert(5)
    assert avl.inorder().count(5) == 1

    # Test 5: delete leaf
    avl.delete(1)
    assert avl.contains(1) is False
    assert _is_balanced(avl._root)

    # Test 6: delete with two children
    avl.delete(5)
    assert avl.contains(5) is False
    assert avl.inorder() == sorted(avl.inorder())  # still sorted
    assert _is_balanced(avl._root)

    # Test 7: delete missing key raises
    try:
        avl.delete(99)
        assert False
    except KeyError:
        pass

    # Test 8: sequential insert triggers rotations (right-skewed)
    avl2 = AVLTree()
    for k in range(1, 16):
        avl2.insert(k)
    assert avl2.inorder() == list(range(1, 16))
    assert _is_balanced(avl2._root)
    assert avl2.height() <= 5   # balanced: ceil(log2(15)) + 1

    # Test 9: reverse sequential insert triggers left rotations
    avl3 = AVLTree()
    for k in range(15, 0, -1):
        avl3.insert(k)
    assert avl3.inorder() == list(range(1, 16))
    assert _is_balanced(avl3._root)

    # Test 10: empty tree height is -1
    empty = AVLTree()
    assert empty.height() == -1

    print("All AVL tree tests passed.")


if __name__ == "__main__":
    test_avl()
    avl = AVLTree()
    for k in [10, 20, 30, 40, 50, 25]:
        avl.insert(k)
    print("Inorder:", avl.inorder())
    print("Height:", avl.height())
