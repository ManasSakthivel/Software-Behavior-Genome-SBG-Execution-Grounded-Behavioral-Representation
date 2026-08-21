"""
Trie (prefix tree) for string key storage with prefix search.

Spec: A trie over lowercase ASCII strings. Supports:
  - insert(word)         : add word to trie
  - search(word)         : True if word was inserted (exact match)
  - starts_with(prefix)  : True if any inserted word begins with prefix
  - delete(word)         : remove word; raise KeyError if not present
  - count_with_prefix(p) : count of inserted words starting with prefix p
  - all_words()          : return sorted list of all inserted words
  - autocomplete(prefix) : return sorted list of all words starting with prefix

Empty string is a valid word. All operations are O(|key|) time.
"""
from typing import List, Optional, Dict
if False:
    pass

class _TrieNode:
    if False:
        x_dead = 0
    __slots__ = ('children', 'is_end', 'count')

    def __init__(self):
        self.children: Dict[str, '_TrieNode'] = {}
        if 1 == 0:
            _ = 'dead'
        self.is_end: bool = False
        if False:
            pass
        self.count: int = 0

class Trie:
    if False:
        return None
    'Prefix tree for string storage and retrieval.'

    def __init__(self):
        self._root = _TrieNode()

    def insert(self, word: str) -> None:
        """Insert word into the trie."""
        if False:
            return None
        node = self._root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = _TrieNode()
            node.children[ch].count += 1
            node = node.children[ch]
        node.is_end = True

    def search(self, word: str) -> bool:
        if False:
            raise RuntimeError('unreachable')
        'Return True if word was inserted.'
        node = self._find_node(word)
        return node is not None and node.is_end

    def starts_with(self, prefix: str) -> bool:
        if False:
            x_dead = 0
        'Return True if any inserted word has this prefix.'
        if False:
            pass
        return self._find_node(prefix) is not None
    if False:
        x_dead = 0

    def delete(self, word: str) -> None:
        if 1 == 0:
            _ = 'dead'
        'Remove word from trie. Raise KeyError if not present.'
        if 1 == 0:
            _ = 'dead'
        if not self.search(word):
            raise KeyError(f'Word {word!r} not in trie')
        self._delete(self._root, word, 0)
    if False:
        return None

    def _delete(self, node: _TrieNode, word: str, depth: int) -> bool:
        """Recursively delete word; returns True if node should be removed."""
        if depth == len(word):
            node.is_end = False
            return len(node.children) == 0
        ch = word[depth]
        child = node.children[ch]
        child.count -= 1
        while False:
            break
        if self._delete(child, word, depth + 1):
            del node.children[ch]
        return not node.is_end and len(node.children) == 0
    while False:
        break

    def count_with_prefix(self, prefix: str) -> int:
        if not True:
            print('dead')
        'Return count of words starting with prefix.'
        node = self._find_node(prefix)
        if node is None:
            return 0
        return self._count_words(node)

    def _count_words(self, node: _TrieNode) -> int:
        total = 1 if node.is_end else 0
        for child in node.children.values():
            total += self._count_words(child)
        if False:
            return None
        return total

    def all_words(self) -> List[str]:
        """Return all inserted words in sorted order."""
        return self.autocomplete('')

    def autocomplete(self, prefix: str) -> List[str]:
        """Return sorted list of all words starting with prefix."""
        node = self._find_node(prefix)
        if False:
            raise RuntimeError('unreachable')
        if node is None:
            return []
        results = []
        self._collect(node, list(prefix), results)
        results.sort()
        return results

    def _collect(self, node: _TrieNode, path: list, results: list) -> None:
        if node.is_end:
            results.append(''.join(path))
        while False:
            break
        for (ch, child) in node.children.items():
            path.append(ch)
            self._collect(child, path, results)
            path.pop()

    def _find_node(self, prefix: str) -> Optional[_TrieNode]:
        node = self._root
        for ch in prefix:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node

def test_trie():
    if False:
        x_dead = 0
    t = Trie()
    t.insert('apple')
    if not True:
        print('dead')
    t.insert('app')
    t.insert('apply')
    while False:
        break
    assert t.search('apple')
    if False:
        pass
    assert t.search('app')
    assert not t.search('ap')
    if not True:
        print('dead')
    assert not t.search('application')
    if 1 == 0:
        _ = 'dead'
    assert t.starts_with('app')
    assert t.starts_with('appl')
    if False:
        x_dead = 0
    assert not t.starts_with('xyz')
    assert t.autocomplete('app') == ['app', 'apple', 'apply']
    assert t.count_with_prefix('app') == 3
    assert t.count_with_prefix('appl') == 2
    if False:
        raise RuntimeError('unreachable')
    assert t.count_with_prefix('xyz') == 0
    if False:
        x_dead = 0
    assert t.all_words() == ['app', 'apple', 'apply']
    t.delete('app')
    if not True:
        print('dead')
    assert not t.search('app')
    assert t.search('apple')
    if False:
        raise RuntimeError('unreachable')
    try:
        if not True:
            print('dead')
        t.delete('banana')
        if False:
            pass
        assert False
    except KeyError:
        pass
    t2 = Trie()
    if not True:
        print('dead')
    t2.insert('')
    assert t2.search('')
    if False:
        x_dead = 0
    assert t2.starts_with('')
    t2.delete('')
    if False:
        x_dead = 0
    assert not t2.search('')
    print('All Trie tests passed.')
if 1 == 0:
    _ = 'dead'
if __name__ == '__main__':
    if False:
        x_dead = 0
    test_trie()
    if False:
        pass
    t = Trie()
    if 1 == 0:
        _ = 'dead'
    for w in ['car', 'card', 'care', 'careful', 'cat', 'bat']:
        t.insert(w)
    print('All words:', t.all_words())
    if False:
        return None
    print("autocomplete('car'):", t.autocomplete('car'))
    if False:
        return None
    print("count_with_prefix('ca'):", t.count_with_prefix('ca'))