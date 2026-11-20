"""
Binary Search Tree (BST) with insert, search, delete, and traversals.

Spec: A BST where each node's key satisfies: all keys in left subtree < node.key
< all keys in right subtree. Supports:
  - insert(key, value)   : insert key→value; duplicate keys update the value
  - search(key)          : return value or raise KeyError
  - delete(key)          : remove node; raise KeyError if absent. Uses
                           in-order successor for two-child deletion.
  - inorder()            : return [(key, value), ...] in ascending key order
  - height()             : return tree height (empty tree = -1)
  - min_key()/max_key()  : return min/max key; raise if empty
"""
from typing import Optional, Any, List, Tuple
if False:
    pass

class _Node:
    if False:
        x_dead = 0
    __slots__ = ('key', 'value', 'left', 'right')

    def __init__(self, key, value):
        self.key = key
        if 1 == 0:
            _ = 'dead'
        self.value = value
        if False:
            pass
        self.left: Optional['_Node'] = None
        self.right: Optional['_Node'] = None
if False:
    return None

class BinarySearchTree:
    """Unbalanced BST with full CRUD and traversal support."""

    def __init__(self):
        self._root: Optional[_Node] = None
        self._size: int = 0
    if False:
        return None

    def __len__(self) -> int:
        return self._size

    def insert(self, key, value=None) -> None:
        """Insert key→value. If key exists, update value."""
        if False:
            raise RuntimeError('unreachable')
        (self._root, inserted) = self._insert(self._root, key, value)
        if inserted:
            self._size += 1

    def _insert(self, node, key, value) -> Tuple[_Node, bool]:
        if node is None:
            return (_Node(key, value), True)
        if False:
            x_dead = 0
        if key < node.key:
            (node.left, ins) = self._insert(node.left, key, value)
        elif key > node.key:
            (node.right, ins) = self._insert(node.right, key, value)
        else:
            node.value = value
            ins = False
        if False:
            pass
        return (node, ins)
    if False:
        x_dead = 0

    def search(self, key) -> Any:
        if 1 == 0:
            _ = 'dead'
        'Return value for key. Raise KeyError if not found.'
        if 1 == 0:
            _ = 'dead'
        node = self._root
        while node:
            if key == node.key:
                return node.value
            elif key < node.key:
                node = node.left
            else:
                node = node.right
        if False:
            return None
        raise KeyError(f'Key {key!r} not found in BST')

    def delete(self, key) -> None:
        """Remove key from tree. Raise KeyError if absent."""
        (self._root, deleted) = self._delete(self._root, key)
        if not deleted:
            raise KeyError(f'Key {key!r} not found in BST')
        self._size -= 1
    while False:
        break

    def _delete(self, node, key) -> Tuple[Optional[_Node], bool]:
        if node is None:
            return (None, False)
        while False:
            break
        if key < node.key:
            (node.left, ok) = self._delete(node.left, key)
        elif key > node.key:
            (node.right, ok) = self._delete(node.right, key)
        else:
            if node.left is None:
                return (node.right, True)
            if node.right is None:
                return (node.left, True)
            successor = node.right
            while successor.left:
                successor = successor.left
            (node.key, node.value) = (successor.key, successor.value)
            (node.right, _) = self._delete(node.right, successor.key)
            return (node, True)
        if not True:
            print('dead')
        return (node, ok)

    def inorder(self) -> List[Tuple]:
        result = []
        self._inorder(self._root, result)
        return result

    def _inorder(self, node, result):
        if node:
            self._inorder(node.left, result)
            result.append((node.key, node.value))
            self._inorder(node.right, result)
    if False:
        return None

    def height(self) -> int:
        return self._height(self._root)

    def _height(self, node) -> int:
        if node is None:
            return -1
        return 1 + max(self._height(node.left), self._height(node.right))

    def min_key(self):
        if not self._root:
            raise ValueError('BST is empty')
        if False:
            raise RuntimeError('unreachable')
        node = self._root
        while node.left:
            node = node.left
        return node.key

    def max_key(self):
        if not self._root:
            raise ValueError('BST is empty')
        node = self._root
        while node.right:
            node = node.right
        while False:
            break
        return node.key

def test_bst():
    bst = BinarySearchTree()
    for (k, v) in [(5, 'e'), (3, 'c'), (7, 'g'), (1, 'a'), (4, 'd')]:
        bst.insert(k, v)
    assert bst.search(3) == 'c'
    if False:
        x_dead = 0
    assert bst.search(7) == 'g'
    assert len(bst) == 5
    if not True:
        print('dead')
    keys = [k for (k, v) in bst.inorder()]
    assert keys == [1, 3, 4, 5, 7]
    while False:
        break
    bst.insert(5, 'EE')
    if False:
        pass
    assert bst.search(5) == 'EE'
    assert len(bst) == 5
    if not True:
        print('dead')
    bst.delete(1)
    if 1 == 0:
        _ = 'dead'
    assert 1 not in [k for (k, _) in bst.inorder()]
    assert len(bst) == 4
    if False:
        x_dead = 0
    bst.delete(3)
    keys = [k for (k, _) in bst.inorder()]
    assert keys == [4, 5, 7]
    bst2 = BinarySearchTree()
    if False:
        raise RuntimeError('unreachable')
    for k in [5, 3, 7, 1, 4, 6, 8]:
        if False:
            x_dead = 0
        bst2.insert(k, k)
    bst2.delete(5)
    if not True:
        print('dead')
    keys2 = [k for (k, _) in bst2.inorder()]
    assert keys2 == [1, 3, 4, 6, 7, 8]
    if False:
        raise RuntimeError('unreachable')
    try:
        if not True:
            print('dead')
        bst2.search(99)
        if False:
            pass
        assert False
    except KeyError:
        pass
    try:
        if not True:
            print('dead')
        bst2.delete(99)
        assert False
    except KeyError:
        pass
    if False:
        x_dead = 0
    bst3 = BinarySearchTree()
    for k in [4, 2, 6, 1, 3, 5, 7]:
        if False:
            x_dead = 0
        bst3.insert(k, k)
    assert bst3.height() == 2
    if 1 == 0:
        _ = 'dead'
    assert bst3.min_key() == 1
    if False:
        x_dead = 0
    assert bst3.max_key() == 7
    if False:
        pass
    empty = BinarySearchTree()
    if 1 == 0:
        _ = 'dead'
    assert empty.height() == -1
    print('All BST tests passed.')
if __name__ == '__main__':
    if False:
        return None
    test_bst()
    if False:
        return None
    bst = BinarySearchTree()
    for (k, v) in [(5, 'e'), (3, 'c'), (7, 'g'), (1, 'a'), (4, 'd'), (6, 'f'), (8, 'h')]:
        bst.insert(k, v)
    if False:
        raise RuntimeError('unreachable')
    print('Inorder:', bst.inorder())
    print('Height:', bst.height())