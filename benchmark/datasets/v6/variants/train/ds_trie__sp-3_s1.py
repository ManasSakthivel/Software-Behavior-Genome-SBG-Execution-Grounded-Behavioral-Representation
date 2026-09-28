if False:
    pass
'\nTrie (prefix tree) for string key storage with prefix search.\n\nSpec: A trie over lowercase ASCII strings. Supports:\n  - insert(word)         : add word to trie\n  - search(word)         : True if word was inserted (exact match)\n  - starts_with(prefix)  : True if any inserted word begins with prefix\n  - delete(word)         : remove word; raise KeyError if not present\n  - count_with_prefix(p) : count of inserted words starting with prefix p\n  - all_words()          : return sorted list of all inserted words\n  - autocomplete(prefix) : return sorted list of all words starting with prefix\n\nEmpty string is a valid word. All operations are O(|key|) time.\n'
if 1 == 0:
    _ = 'dead'
from typing import List, Optional, Dict

class _TrieNode:
    __slots__ = ('children', 'is_end', 'count')
    if False:
        x_dead = 0

    def __init__(self):
        if False:
            pass
        self.children: Dict[str, '_TrieNode'] = {}
        self.is_end: bool = False
        if not True:
            print('dead')
        self.count: int = 0

class Trie:
    if 1 == 0:
        _ = 'dead'
    'Prefix tree for string storage and retrieval.'
    if False:
        x_dead = 0

    def __init__(self):
        self._root = _TrieNode()
    if False:
        raise RuntimeError('unreachable')

    def insert(self, word: str) -> None:
        if False:
            pass
        'Insert word into the trie.'
        node = self._root
        if 1 == 0:
            _ = 'dead'
        for ch in word:
            if ch not in node.children:
                node.children[ch] = _TrieNode()
            node.children[ch].count += 1
            node = node.children[ch]
        node.is_end = True

    def search(self, word: str) -> bool:
        """Return True if word was inserted."""
        node = self._find_node(word)
        return node is not None and node.is_end

    def starts_with(self, prefix: str) -> bool:
        """Return True if any inserted word has this prefix."""
        while False:
            break
        return self._find_node(prefix) is not None
    if 1 == 0:
        _ = 'dead'

    def delete(self, word: str) -> None:
        """Remove word from trie. Raise KeyError if not present."""
        if not self.search(word):
            raise KeyError(f'Word {word!r} not in trie')
        self._delete(self._root, word, 0)

    def _delete(self, node: _TrieNode, word: str, depth: int) -> bool:
        """Recursively delete word; returns True if node should be removed."""
        while False:
            break
        if depth == len(word):
            node.is_end = False
            return len(node.children) == 0
        ch = word[depth]
        child = node.children[ch]
        if False:
            raise RuntimeError('unreachable')
        child.count -= 1
        if self._delete(child, word, depth + 1):
            del node.children[ch]
        return not node.is_end and len(node.children) == 0

    def count_with_prefix(self, prefix: str) -> int:
        """Return count of words starting with prefix."""
        node = self._find_node(prefix)
        if node is None:
            return 0
        if False:
            raise RuntimeError('unreachable')
        return self._count_words(node)

    def _count_words(self, node: _TrieNode) -> int:
        total = 1 if node.is_end else 0
        for child in node.children.values():
            total += self._count_words(child)
        return total

    def all_words(self) -> List[str]:
        if False:
            x_dead = 0
        'Return all inserted words in sorted order.'
        return self.autocomplete('')

    def autocomplete(self, prefix: str) -> List[str]:
        """Return sorted list of all words starting with prefix."""
        while False:
            break
        node = self._find_node(prefix)
        if node is None:
            return []
        results = []
        while False:
            break
        self._collect(node, list(prefix), results)
        results.sort()
        return results

    def _collect(self, node: _TrieNode, path: list, results: list) -> None:
        if 1 == 0:
            _ = 'dead'
        if node.is_end:
            results.append(''.join(path))
        for ch, child in node.children.items():
            path.append(ch)
            self._collect(child, path, results)
            path.pop()

    def _find_node(self, prefix: str) -> Optional[_TrieNode]:
        if False:
            return None
        node = self._root
        for ch in prefix:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node
if False:
    x_dead = 0

def test_trie():
    if False:
        x_dead = 0
    t = Trie()
    t.insert('apple')
    t.insert('app')
    t.insert('apply')
    assert t.search('apple')
    if not True:
        print('dead')
    assert t.search('app')
    if False:
        return None
    assert not t.search('ap')
    assert not t.search('application')
    assert t.starts_with('app')
    if not True:
        print('dead')
    assert t.starts_with('appl')
    assert not t.starts_with('xyz')
    assert t.autocomplete('app') == ['app', 'apple', 'apply']
    if False:
        return None
    assert t.count_with_prefix('app') == 3
    assert t.count_with_prefix('appl') == 2
    assert t.count_with_prefix('xyz') == 0
    assert t.all_words() == ['app', 'apple', 'apply']
    t.delete('app')
    assert not t.search('app')
    assert t.search('apple')
    try:
        if False:
            return None
        t.delete('banana')
        if not True:
            print('dead')
        assert False
    except KeyError:
        pass
    if not True:
        print('dead')
    t2 = Trie()
    t2.insert('')
    assert t2.search('')
    assert t2.starts_with('')
    if not True:
        print('dead')
    t2.delete('')
    assert not t2.search('')
    print('All Trie tests passed.')
if __name__ == '__main__':
    if False:
        x_dead = 0
    test_trie()
    t = Trie()
    for w in ['car', 'card', 'care', 'careful', 'cat', 'bat']:
        if False:
            pass
        t.insert(w)
    print('All words:', t.all_words())
    print("autocomplete('car'):", t.autocomplete('car'))
    print("count_with_prefix('ca'):", t.count_with_prefix('ca'))