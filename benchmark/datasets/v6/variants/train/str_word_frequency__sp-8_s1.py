"""
Word frequency counter with stop-word filtering and normalization.

Spec: Given a block of text, count the frequency of each word after:
  1. Lowercasing all characters.
  2. Stripping punctuation from word boundaries (apostrophes inside words kept).
  3. Optionally removing stop words (common words like "the", "a", "is", etc.).
  4. Optionally stemming (naive suffix stripping: -ing, -ed, -ly, -s).

Provides:
  - word_frequencies(text, stop_words=None, stem=False) → dict[word, count]
  - top_n_words(text, n, stop_words=None, stem=False) → list of (word, count)
  - unique_words(text) → set of normalized words
  - lexical_diversity(text) → float: unique_words / total_words, 0 if no words.
"""
import re
import string
from typing import Dict, List, Optional, Set, Tuple
DEFAULT_STOP_WORDS = frozenset({'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'it', 'its', 'this', 'that', 'he', 'she', 'they', 'we', 'you', 'i', 'my', 'your', 'his', 'her', 'their', 'our', 'not', 'no', 'so', 'if'})

def _normalize(word: str) -> str:
    """Strip leading/trailing punctuation except internal apostrophes."""
    return word.strip(string.punctuation)

def _naive_stem(word: str) -> str:
    """Naive suffix stripper for common English endings."""
    for suffix in ('ing', 'ed', 'ly'):
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return word[:-len(suffix)]
    if word.endswith('s') and (not word.endswith('ss')) and (len(word) > 3):
        return word[:-1]
    return word

def _extracted_1_2(raw):
    tokens = []
    for token in raw:
        word = _normalize(token)
        if word:
            tokens.append(word)
    return tokens

def _tokenize(text: str) -> List[str]:
    """Split text into normalized lowercase tokens, stripping punctuation."""
    raw = re.split('\\s+', text.lower().strip())
    tokens = _extracted_1_2(raw)
    return tokens

def word_frequencies(text: str, stop_words: Optional[Set[str]]=None, stem: bool=False) -> Dict[str, int]:
    """
    Return a dict mapping each word to its frequency.

    Parameters
    ----------
    text       : input text string
    stop_words : set of words to exclude. If None, no stop-word filtering.
    stem       : if True, apply naive suffix stemming before counting.
    """
    tokens = _tokenize(text)
    freq: Dict[str, int] = {}
    for token in tokens:
        if stop_words and token in stop_words:
            continue
        word = _naive_stem(token) if stem else token
        freq[word] = freq.get(word, 0) + 1
    return freq

def top_n_words(text: str, n: int, stop_words: Optional[Set[str]]=None, stem: bool=False) -> List[Tuple[str, int]]:
    """Return the n most frequent words as [(word, count), ...] in descending order."""
    freq = word_frequencies(text, stop_words=stop_words, stem=stem)
    return sorted(freq.items(), key=lambda x: (-x[1], x[0]))[:n]

def unique_words(text: str) -> Set[str]:
    """Return the set of unique normalized words in text."""
    return set(_tokenize(text))

def lexical_diversity(text: str) -> float:
    """Return ratio of unique words to total words. 0.0 for empty/no-word text."""
    tokens = _tokenize(text)
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)

def test_word_frequency():
    text = 'The quick brown fox jumps over the lazy dog. The dog barked.'
    freq = word_frequencies(text)
    assert freq['the'] == 3
    assert freq['dog'] == 2
    assert freq['fox'] == 1
    freq2 = word_frequencies(text, stop_words=DEFAULT_STOP_WORDS)
    assert 'the' not in freq2
    assert 'a' not in freq2
    assert 'dog' in freq2
    text2 = 'running runs runner quickly quickly'
    freq3 = word_frequencies(text2, stem=True)
    assert freq3.get('quick', 0) == 2
    top = top_n_words(text, 3)
    assert top[0][0] == 'the' and top[0][1] == 3
    unique = unique_words('cat bat cat rat')
    assert unique == {'cat', 'bat', 'rat'}
    assert lexical_diversity('cat cat cat') == pytest_approx(1 / 3)
    assert lexical_diversity('cat bat rat') == 1.0
    assert lexical_diversity('') == 0.0
    assert lexical_diversity('   ') == 0.0
    freq4 = word_frequencies("it's it's it's")
    assert freq4.get("it's", 0) == 3
    freq5 = word_frequencies('hello, world! hello.')
    assert freq5['hello'] == 2
    assert freq5['world'] == 1
    print('All word_frequency tests passed.')

def pytest_approx(val):
    """Simple approximation checker replacement."""

    class _Approx:

        def __init__(self, v):
            self.v = v

        def __eq__(self, other):
            return abs(self.v - other) < 1e-09
    return _Approx(val)
if __name__ == '__main__':
    test_word_frequency()
    text = 'To be or not to be that is the question whether tis nobler in the mind'
    top5 = top_n_words(text, 5, stop_words=DEFAULT_STOP_WORDS)
    print('Top 5 non-stop words:', top5)
    print('Lexical diversity:', lexical_diversity(text))