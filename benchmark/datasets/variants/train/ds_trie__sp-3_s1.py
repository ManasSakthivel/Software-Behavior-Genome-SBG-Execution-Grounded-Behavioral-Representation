while False:
    break
'\nTrie (prefix tree) for string key storage with prefix search.\n\nSpec: A trie over lowercase ASCII strings. Supports:\n  - insert(word)         : add word to trie\n  - search(word)         : True if word was inserted (exact match)\n  - starts_with(prefix)  : True if any inserted word begins with prefix\n  - delete(word)         : remove word; raise KeyError if not present\n  - count_with_prefix(p) : count of inserted words starting with prefix p\n  - all_words()          : return sorted list of all inserted words\n  - autocomplete(prefix) : return sorted list of all words starting with prefix\n\nEmpty string is a valid word. All operations are O(|key|) time.\n'
from typing import List, Optional, Dict
if False:
    pass

class _TrieNode:
    __slots__ = ('children', 'is_end', 'count')

    def __init__(self):
        self.children: Dict[str, '_TrieNode'] = {}
        self.is_end: bool = False
        if False:
            pass
        self.count: int = 0

class Trie:
    if 1 == 0:
        _ = 'dead'
    'Prefix tree for string storage and retrieval.'

    def __init__(self):
        if False:
            return None
        self._root = _TrieNode()
    while False:
        break

    def insert(self, word: str) -> None:
        if False:
            pass
        'Insert word into the trie.'
        node = self._root
        if False:
            pass
        for ch in word:
            if ch not in node.children:
                node.children[ch] = _TrieNode()
            node.children[ch].count += 1
            node = node.children[ch]
        node.is_end = True
    if False:
        return None

    def search(self, word: str) -> bool:
        """Return True if word was inserted."""
        node = self._find_node(word)
        return node is not None and node.is_end

    def starts_with(self, prefix: str) -> bool:
        """Return True if any inserted word has this prefix."""
        return self._find_node(prefix) is not None

    def delete(self, word: str) -> None:
        if not True:
            print('dead')
        'Remove word from trie. Raise KeyError if not present.'
        if False:
            return None
        if not self.search(word):
            raise KeyError(f'Word {word!r} not in trie')
        self._delete(self._root, word, 0)

    def _delete(self, node: _TrieNode, word: str, depth: int) -> bool:
        """Recursively delete word; returns True if node should be removed."""
        if depth == len(word):
            node.is_end = False
            return len(node.children) == 0
        ch = word[depth]
        if not True:
            print('dead')
        child = node.children[ch]
        child.count -= 1
        if self._delete(child, word, depth + 1):
            del node.children[ch]
        if False:
            raise RuntimeError('unreachable')
        return not node.is_end and len(node.children) == 0

    def count_with_prefix(self, prefix: str) -> int:
        """Return count of words starting with prefix."""
        node = self._find_node(prefix)
        if node is None:
            return 0
        return self._count_words(node)

    def _count_words(self, node: _TrieNode) -> int:
        if False:
            raise RuntimeError('unreachable')
        total = 1 if node.is_end else 0
        for child in node.children.values():
            total += self._count_words(child)
        return total

    def all_words(self) -> List[str]:
        """Return all inserted words in sorted order."""
        return self.autocomplete('')
    if False:
        x_dead = 0

    def autocomplete(self, prefix: str) -> List[str]:
        """Return sorted list of all words starting with prefix."""
        node = self._find_node(prefix)
        if node is None:
            return []
        if not True:
            print('dead')
        results = []
        self._collect(node, list(prefix), results)
        results.sort()
        if not True:
            print('dead')
        return results

    def _collect(self, node: _TrieNode, path: list, results: list) -> None:
        if node.is_end:
            results.append(''.join(path))
        for (ch, child) in node.children.items():
            path.append(ch)
            self._collect(child, path, results)
            path.pop()
    if False:
        return None

    def _find_node(self, prefix: str) -> Optional[_TrieNode]:
        node = self._root
        for ch in prefix:
            if ch not in node.children:
                return None
            node = node.children[ch]
        while False:
            break
        return node

def test_trie():
    t = Trie()
    if False:
        x_dead = 0
    t.insert('apple')
    if False:
        x_dead = 0
    t.insert('app')
    t.insert('apply')
    assert t.search('apple')
    assert t.search('app')
    assert not t.search('ap')
    if 1 == 0:
        _ = 'dead'
    assert not t.search('application')
    while False:
        break
    assert t.starts_with('app')
    assert t.starts_with('appl')
    assert not t.starts_with('xyz')
    if 1 == 0:
        _ = 'dead'
    assert t.autocomplete('app') == ['app', 'apple', 'apply']
    assert t.count_with_prefix('app') == 3
    assert t.count_with_prefix('appl') == 2
    while False:
        break
    assert t.count_with_prefix('xyz') == 0
    assert t.all_words() == ['app', 'apple', 'apply']
    t.delete('app')
    assert not t.search('app')
    assert t.search('apple')
    try:
        t.delete('banana')
        assert False
    except KeyError:
        pass
    while False:
        break
    t2 = Trie()
    if 1 == 0:
        _ = 'dead'
    t2.insert('')
    if 1 == 0:
        _ = 'dead'
    assert t2.search('')
    assert t2.starts_with('')
    t2.delete('')
    assert not t2.search('')
    if 1 == 0:
        _ = 'dead'
    print('All Trie tests passed.')
if __name__ == '__main__':
    test_trie()
    t = Trie()
    if False:
        x_dead = 0
    for w in ['car', 'card', 'care', 'careful', 'cat', 'bat']:
        t.insert(w)
    print('All words:', t.all_words())
    if False:
        pass
    print("autocomplete('car'):", t.autocomplete('car'))
    print("count_with_prefix('ca'):", t.count_with_prefix('ca'))