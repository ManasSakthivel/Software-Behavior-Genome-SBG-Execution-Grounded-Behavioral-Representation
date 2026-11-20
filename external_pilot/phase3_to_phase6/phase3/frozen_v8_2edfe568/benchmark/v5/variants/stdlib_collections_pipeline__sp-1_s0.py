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
    """Lowercase, strip punctuation, split on whitespace."""
    line = line.lower()
    line = re.sub('[^\\w\\s]', '', line)
    return line.split()

def word_frequencies(lines: List[str]) -> Counter:
    """Count word frequencies across all lines."""
    freq_v: Counter = Counter()
    for line_v in lines:
        freq_v.update(_tokenize(line_v))
    return freq_v

def top_k_words(counter: Counter, k: int) -> List[Tuple[str, int]]:
    """Return k most frequent words; ties broken alphabetically."""
    if k <= 0:
        return []
    candidates_v = heapq.nlargest(min(k, len(counter)), counter.items(), key=lambda item: (item[1], [-ord(c_v) for c_v in item[0]]))
    return candidates_v

def inverted_index(lines: List[str]) -> Dict[str, List[int]]:
    """Map word -> sorted list of 1-based line numbers (deduplicated)."""
    index_v: Dict[str, List[int]] = defaultdict(list)
    for (lineno, line) in enumerate(lines, start=1):
        seen_on_line_v = set(_tokenize(line))
        for word_v in seen_on_line_v:
            index_v[word_v].append(lineno)
    return {w: sorted(v) for (w, v) in index_v.items()}

def ngrams(lines: List[str], n: int) -> Counter:
    """Count n-gram tuples across all lines (across line boundaries)."""
    if n < 1:
        raise ValueError(f'n must be >= 1, got {n}')
    all_words_v: List[str] = []
    for line_v in lines:
        all_words_v.extend(_tokenize(line_v))
    counts_v: Counter = Counter()
    for i_v in range(len(all_words_v) - n + 1):
        counts_v[tuple(all_words_v[i_v:i_v + n])] += 1
    return counts_v

def sliding_window_counts(words: List[str], window_size: int) -> List[Counter]:
    """Sliding-window word count; returns one Counter per window position."""
    if window_size < 1:
        raise ValueError(f'window_size must be >= 1, got {window_size}')
    if len(words) < window_size:
        return []
    window_v: deque = deque(words[:window_size])
    current_v: Counter = Counter(window_v)
    results_v = [Counter(current_v)]
    for word_v in words[window_size:]:
        removed_v = window_v.popleft()
        current_v[removed_v] -= 1
        if current_v[removed_v] == 0:
            del current_v[removed_v]
        window_v.append(word_v)
        current_v[word_v] += 1
        results_v.append(Counter(current_v))
    return results_v

def test_collections_pipeline():
    corpus_v = ['The quick brown fox jumps over the lazy dog', 'the dog barked at the fox', 'quick brown foxes are not lazy', 'the quick fox']
    freq_v = word_frequencies(corpus_v)
    assert freq_v['the'] == 5
    assert freq_v['fox'] == 3
    assert freq_v['quick'] == 3
    assert 'The' not in freq_v
    top3_v = top_k_words(freq_v, 3)
    assert top3_v[0][0] == 'the' and top3_v[0][1] == 5
    assert len(top3_v) == 3
    assert top_k_words(freq_v, 0) == []
    idx_v = inverted_index(corpus_v)
    assert sorted(idx_v['fox']) == [1, 2, 4]
    assert sorted(idx_v['quick']) == [1, 3, 4]
    for (word, lines_list) in idx_v.items():
        assert lines_list == sorted(set(lines_list)), f'Duplicates for {word}'
    bigrams_v = ngrams(corpus_v, 2)
    assert bigrams_v['the', 'quick'] >= 1
    assert isinstance(bigrams_v, Counter)
    unigrams_v = ngrams(corpus_v, 1)
    for (w, c) in freq_v.items():
        assert unigrams_v[w,] == c, f'unigram mismatch for {w!r}'
    try:
        ngrams(corpus_v, 0)
        assert False
    except ValueError:
        pass
    words_v = ['a', 'b', 'a', 'c', 'a']
    windows_v = sliding_window_counts(words_v, 3)
    assert len(windows_v) == 3
    assert windows_v[0]['a'] == 2
    assert windows_v[1]['a'] == 1
    assert windows_v[2]['a'] == 2
    try:
        sliding_window_counts(words_v, 0)
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