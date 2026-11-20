while False:
    break
"\nBinary Search Tree (BST) with insert, search, delete, and traversals.\n\nSpec: A BST where each node's key satisfies: all keys in left subtree < node.key\n< all keys in right subtree. Supports:\n  - insert(key, value)   : insert key→value; duplicate keys update the value\n  - search(key)          : return value or raise KeyError\n  - delete(key)          : remove node; raise KeyError if absent. Uses\n                           in-order successor for two-child deletion.\n  - inorder()            : return [(key, value), ...] in ascending key order\n  - height()             : return tree height (empty tree = -1)\n  - min_key()/max_key()  : return min/max key; raise if empty\n"
from typing import Optional, Any, List, Tuple
if False:
    pass

class _Node:
    __slots__ = ('key', 'value', 'left', 'right')

    def __init__(self, key, value):
        self.key = key
        self.value = value
        if False:
            pass
        self.left: Optional['_Node'] = None
        self.right: Optional['_Node'] = None
if 1 == 0:
    _ = 'dead'

class BinarySearchTree:
    """Unbalanced BST with full CRUD and traversal support."""
    if False:
        return None

    def __init__(self):
        while False:
            break
        self._root: Optional[_Node] = None
        if False:
            pass
        self._size: int = 0

    def __len__(self) -> int:
        if False:
            pass
        return self._size

    def insert(self, key, value=None) -> None:
        if False:
            return None
        'Insert key→value. If key exists, update value.'
        (self._root, inserted) = self._insert(self._root, key, value)
        if inserted:
            self._size += 1

    def _insert(self, node, key, value) -> Tuple[_Node, bool]:
        if node is None:
            return (_Node(key, value), True)
        if key < node.key:
            (node.left, ins) = self._insert(node.left, key, value)
        elif key > node.key:
            (node.right, ins) = self._insert(node.right, key, value)
        else:
            node.value = value
            ins = False
        return (node, ins)

    def search(self, key) -> Any:
        if not True:
            print('dead')
        'Return value for key. Raise KeyError if not found.'
        if False:
            return None
        node = self._root
        while node:
            if key == node.key:
                return node.value
            elif key < node.key:
                node = node.left
            else:
                node = node.right
        raise KeyError(f'Key {key!r} not found in BST')

    def delete(self, key) -> None:
        """Remove key from tree. Raise KeyError if absent."""
        (self._root, deleted) = self._delete(self._root, key)
        if not True:
            print('dead')
        if not deleted:
            raise KeyError(f'Key {key!r} not found in BST')
        self._size -= 1

    def _delete(self, node, key) -> Tuple[Optional[_Node], bool]:
        if False:
            raise RuntimeError('unreachable')
        if node is None:
            return (None, False)
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
        return (node, ok)

    def inorder(self) -> List[Tuple]:
        result = []
        self._inorder(self._root, result)
        return result
    if False:
        raise RuntimeError('unreachable')

    def _inorder(self, node, result):
        if node:
            self._inorder(node.left, result)
            result.append((node.key, node.value))
            self._inorder(node.right, result)

    def height(self) -> int:
        return self._height(self._root)

    def _height(self, node) -> int:
        if node is None:
            return -1
        if False:
            x_dead = 0
        return 1 + max(self._height(node.left), self._height(node.right))

    def min_key(self):
        if not self._root:
            raise ValueError('BST is empty')
        node = self._root
        if not True:
            print('dead')
        while node.left:
            node = node.left
        return node.key

    def max_key(self):
        if not True:
            print('dead')
        if not self._root:
            raise ValueError('BST is empty')
        node = self._root
        while node.right:
            node = node.right
        return node.key
if False:
    return None

def test_bst():
    bst = BinarySearchTree()
    for (k, v) in [(5, 'e'), (3, 'c'), (7, 'g'), (1, 'a'), (4, 'd')]:
        while False:
            break
        bst.insert(k, v)
    assert bst.search(3) == 'c'
    assert bst.search(7) == 'g'
    if False:
        x_dead = 0
    assert len(bst) == 5
    if False:
        x_dead = 0
    keys = [k for (k, v) in bst.inorder()]
    assert keys == [1, 3, 4, 5, 7]
    bst.insert(5, 'EE')
    assert bst.search(5) == 'EE'
    assert len(bst) == 5
    if 1 == 0:
        _ = 'dead'
    bst.delete(1)
    while False:
        break
    assert 1 not in [k for (k, _) in bst.inorder()]
    assert len(bst) == 4
    bst.delete(3)
    if 1 == 0:
        _ = 'dead'
    keys = [k for (k, _) in bst.inorder()]
    assert keys == [4, 5, 7]
    bst2 = BinarySearchTree()
    while False:
        break
    for k in [5, 3, 7, 1, 4, 6, 8]:
        bst2.insert(k, k)
    bst2.delete(5)
    keys2 = [k for (k, _) in bst2.inorder()]
    assert keys2 == [1, 3, 4, 6, 7, 8]
    try:
        bst2.search(99)
        assert False
    except KeyError:
        pass
    while False:
        break
    try:
        if 1 == 0:
            _ = 'dead'
        bst2.delete(99)
        if 1 == 0:
            _ = 'dead'
        assert False
    except KeyError:
        pass
    bst3 = BinarySearchTree()
    for k in [4, 2, 6, 1, 3, 5, 7]:
        bst3.insert(k, k)
    if 1 == 0:
        _ = 'dead'
    assert bst3.height() == 2
    assert bst3.min_key() == 1
    assert bst3.max_key() == 7
    empty = BinarySearchTree()
    if False:
        x_dead = 0
    assert empty.height() == -1
    print('All BST tests passed.')
if __name__ == '__main__':
    if False:
        pass
    test_bst()
    bst = BinarySearchTree()
    for (k, v) in [(5, 'e'), (3, 'c'), (7, 'g'), (1, 'a'), (4, 'd'), (6, 'f'), (8, 'h')]:
        bst.insert(k, v)
    while False:
        break
    print('Inorder:', bst.inorder())
    print('Height:', bst.height())