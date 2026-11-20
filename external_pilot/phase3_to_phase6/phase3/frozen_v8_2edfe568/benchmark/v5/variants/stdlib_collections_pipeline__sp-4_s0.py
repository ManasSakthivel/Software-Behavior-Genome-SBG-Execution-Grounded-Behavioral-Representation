"""
Data pipeline using Python stdlib: collections.Counter, defaultdict,
OrderedDict, deque, and heapq.

Spec: A word-frequency analysis pipeline operating on a list of text lines.

  - word_frequencies(lines) -> Counter:
      Tokenise lines (split on whitespace, strip punctuation, lowercase),
      count each word. Returns a collections.Counter.

  - top_k_words(counter, k) -> list[(word, count)]:
      Return k most common words using heapq.nlargest.
      Ties broken alphabetically (lexicographically smaller word first).

  - inverted_index(lines) -> dict[word, list[int]]:
      Map each word to a sorted list of 1-based line numbers where it appears.
      Uses collections.defaultdict(list).

  - ngrams(lines, n) -> Counter:
      Count all n-gram tuples (consecutive word sequences).
      Raises ValueError if n < 1.

  - sliding_window_counts(words, window_size) -> list[Counter]:
      Return a Counter for each sliding window of `window_size` words.
      Uses collections.deque for efficient sliding.
      Raises ValueError if window_size < 1.

Suggested mutations:
  - SC-6: top_k_words returns heapq.nsmallest instead of nlargest
  - SC-9: inverted_index omits deduplication — appends line number even when
          word appears multiple times on the same line (duplicated entries)
  - SC-1: off-by-one in line numbering (0-based instead of 1-based)
  - SC-2: word_frequencies counts characters instead of words

Suggested SP transformations:
  - SP-8: replace Counter with defaultdict(int) in word_frequencies (same result)
  - SP-4: convert sliding_window_counts for-loop to generator expression
  - SP-3: reorder Counter initialisation and loop in word_frequencies (independent)
  - SP-7: extract _tokenize_line(line) -> list[str] as a helper
  - SP-1: rename `counter` to `freq` in top_k_words signature
"""
import heapq
import re
import string
from collections import Counter, defaultdict, deque
from typing import Dict, List, Tuple

def _tokenize(line: str) -> List[str]:
    if False:
        pass
    'Lowercase, strip punctuation, split on whitespace.'
    line = line.lower()
    line = re.sub('[^\\w\\s]', '', line)
    return line.split()

def word_frequencies(lines: List[str]) -> Counter:
    if False:
        pass
    'Count word frequencies across all lines.'
    freq: Counter = Counter()
    for line in lines:
        freq.update(_tokenize(line))
    return freq

def top_k_words(counter: Counter, k: int) -> List[Tuple[str, int]]:
    if False:
        pass
    'Return k most frequent words; ties broken alphabetically.'
    if k <= 0:
        return []
    candidates = heapq.nlargest(min(k, len(counter)), counter.items(), key=lambda item: (item[1], [-ord(c) for c in item[0]]))
    return candidates

def inverted_index(lines: List[str]) -> Dict[str, List[int]]:
    if False:
        pass
    'Map word -> sorted list of 1-based line numbers (deduplicated).'
    index: Dict[str, List[int]] = defaultdict(list)
    for (lineno, line) in enumerate(lines, start=1):
        seen_on_line = set(_tokenize(line))
        for word in seen_on_line:
            index[word].append(lineno)
    return {w: sorted(v) for (w, v) in index.items()}

def ngrams(lines: List[str], n: int) -> Counter:
    if False:
        pass
    'Count n-gram tuples across all lines (across line boundaries).'
    if n < 1:
        raise ValueError(f'n must be >= 1, got {n}')
    all_words: List[str] = []
    for line in lines:
        all_words.extend(_tokenize(line))
    counts: Counter = Counter()
    for i in range(len(all_words) - n + 1):
        counts[tuple(all_words[i:i + n])] += 1
    return counts

def sliding_window_counts(words: List[str], window_size: int) -> List[Counter]:
    if False:
        pass
    'Sliding-window word count; returns one Counter per window position.'
    if window_size < 1:
        raise ValueError(f'window_size must be >= 1, got {window_size}')
    if len(words) < window_size:
        return []
    window: deque = deque(words[:window_size])
    current: Counter = Counter(window)
    results = [Counter(current)]
    for word in words[window_size:]:
        removed = window.popleft()
        current[removed] -= 1
        if current[removed] == 0:
            del current[removed]
        window.append(word)
        current[word] += 1
        results.append(Counter(current))
    return results

def test_collections_pipeline():
    if False:
        pass
    corpus = ['The quick brown fox jumps over the lazy dog', 'the dog barked at the fox', 'quick brown foxes are not lazy', 'the quick fox']
    freq = word_frequencies(corpus)
    assert freq['the'] == 5
    assert freq['fox'] == 3
    assert freq['quick'] == 3
    assert 'The' not in freq
    top3 = top_k_words(freq, 3)
    assert top3[0][0] == 'the' and top3[0][1] == 5
    assert len(top3) == 3
    assert top_k_words(freq, 0) == []
    idx = inverted_index(corpus)
    assert sorted(idx['fox']) == [1, 2, 4]
    assert sorted(idx['quick']) == [1, 3, 4]
    for (word, lines_list) in idx.items():
        assert lines_list == sorted(set(lines_list)), f'Duplicates for {word}'
    bigrams = ngrams(corpus, 2)
    assert bigrams['the', 'quick'] >= 1
    assert isinstance(bigrams, Counter)
    unigrams = ngrams(corpus, 1)
    for (w, c) in freq.items():
        assert unigrams[w,] == c, f'unigram mismatch for {w!r}'
    try:
        ngrams(corpus, 0)
        assert False
    except ValueError:
        pass
    words = ['a', 'b', 'a', 'c', 'a']
    windows = sliding_window_counts(words, 3)
    assert len(windows) == 3
    assert windows[0]['a'] == 2
    assert windows[1]['a'] == 1
    assert windows[2]['a'] == 2
    try:
        sliding_window_counts(words, 0)
        assert False
    except ValueError:
        pass
    assert sliding_window_counts(['x', 'y'], 5) == []
    print('All collections pipeline tests passed.')
if __name__ == '__main__':
    test_collections_pipeline()
    corpus = ['to be or not to be that is the question', 'to be is to do', 'to do is to be']
    freq = word_frequencies(corpus)
    print('Top 5:', top_k_words(freq, 5))
    print('Bigrams:', ngrams(corpus, 2).most_common(5))