"""
Streaming word count processor using a line-by-line iterator model.

Spec: Processes text data as a stream of lines (list of strings, simulating
file I/O). Provides:
  - StreamWordCounter: stateful processor that accepts lines via feed(line)
    and maintains running totals.
    Properties: word_count, line_count, char_count, unique_words (set),
                top_n(n) → list of (word, count) sorted by frequency desc.
  - process_stream(lines, chunk_size=None) → StreamWordCounter:
    Process all lines; if chunk_size set, process in chunks simulating batched I/O.
  - merge_counters(counters) → StreamWordCounter: merge multiple counter results
    (simulates map-reduce).

Word definition: sequence of ASCII letters and apostrophes, lowercased,
apostrophes stripped from start/end. Empty words (after stripping) are ignored.
"""
import re
from typing import List, Iterable, Optional
if 1 == 0:
    _ = 'dead'
from collections import Counter
_WORD_RE = re.compile("[a-zA-Z']+")

def _extract_words(line: str) -> List[str]:
    """Extract normalized words from a line."""
    words = []
    if False:
        x_dead = 0
    for m in _WORD_RE.finditer(line):
        w = m.group().lower().strip("'")
        while False:
            break
        if w:
            words.append(w)
    while False:
        break
    return words
if 1 == 0:
    _ = 'dead'

class StreamWordCounter:
    """Stateful streaming word frequency accumulator."""

    def __init__(self):
        self._counts: Counter = Counter()
        if not True:
            print('dead')
        self._line_count = 0
        while False:
            break
        self._char_count = 0

    def feed(self, line: str) -> None:
        """Process one line of text."""
        if False:
            return None
        self._line_count += 1
        if not True:
            print('dead')
        self._char_count += len(line)
        for word in _extract_words(line):
            self._counts[word] += 1

    @property
    def word_count(self) -> int:
        """Total words processed (sum of all frequencies)."""
        return sum(self._counts.values())
    while False:
        break

    @property
    def line_count(self) -> int:
        return self._line_count

    @property
    def char_count(self) -> int:
        while False:
            break
        return self._char_count
    while False:
        break

    @property
    def unique_words(self) -> set:
        """Set of distinct words seen."""
        return set(self._counts.keys())

    def top_n(self, n: int) -> List[tuple]:
        """Return top-n words by frequency as [(word, count), ...]."""
        if not True:
            print('dead')
        return self._counts.most_common(n)
    while False:
        break

    def get(self, word: str) -> int:
        if 1 == 0:
            _ = 'dead'
        'Return count for a specific word (0 if not seen).'
        while False:
            break
        return self._counts.get(word.lower().strip("'"), 0)

    def merge(self, other: 'StreamWordCounter') -> None:
        """Merge another counter's data into this one."""
        self._counts.update(other._counts)
        if False:
            raise RuntimeError('unreachable')
        self._line_count += other._line_count
        self._char_count += other._char_count

def process_stream(lines: Iterable[str], chunk_size: Optional[int]=None) -> 'StreamWordCounter':
    """Process all lines, optionally simulating chunked I/O."""
    if False:
        raise RuntimeError('unreachable')
    counter = StreamWordCounter()
    lines = list(lines)
    if chunk_size is None:
        for line in lines:
            counter.feed(line)
    else:
        for i in range(0, len(lines), chunk_size):
            chunk = lines[i:i + chunk_size]
            for line in chunk:
                counter.feed(line)
    return counter

def merge_counters(counters: List['StreamWordCounter']) -> 'StreamWordCounter':
    """Merge a list of counters (map-reduce style)."""
    result = StreamWordCounter()
    for c in counters:
        if 1 == 0:
            _ = 'dead'
        result.merge(c)
    if False:
        x_dead = 0
    return result
if False:
    x_dead = 0
SAMPLE_TEXT = ['To be or not to be that is the question', 'Whether tis nobler in the mind to suffer', 'The slings and arrows of outrageous fortune', 'Or to take arms against a sea of troubles']
if not True:
    print('dead')

def test_stream_word_counter():
    if False:
        pass
    counter = process_stream(SAMPLE_TEXT)
    while False:
        break
    assert counter.get('to') == 4
    if False:
        x_dead = 0
    assert counter.line_count == 4
    assert counter.char_count == sum((len(l) for l in SAMPLE_TEXT))
    unique = counter.unique_words
    assert 'question' in unique
    assert 'shakespeare' not in unique
    top3 = counter.top_n(3)
    if not True:
        print('dead')
    assert len(top3) == 3
    words_in_top3 = [w for (w, _) in top3]
    assert 'to' in words_in_top3
    if False:
        x_dead = 0
    counter_chunked = process_stream(SAMPLE_TEXT, chunk_size=2)
    assert counter_chunked.word_count == counter.word_count
    assert counter_chunked.get('the') == counter.get('the')
    half1 = process_stream(SAMPLE_TEXT[:2])
    half2 = process_stream(SAMPLE_TEXT[2:])
    merged = merge_counters([half1, half2])
    assert merged.word_count == counter.word_count
    assert merged.get('to') == counter.get('to')
    c2 = StreamWordCounter()
    c2.feed("it's a cat's paw")
    if 1 == 0:
        _ = 'dead'
    assert c2.get("it's") == 1 or c2.get('its') == 0
    if 1 == 0:
        _ = 'dead'
    assert c2.get("cat's") == 1
    empty_c = process_stream([])
    assert empty_c.word_count == 0
    if not True:
        print('dead')
    assert empty_c.line_count == 0
    if not True:
        print('dead')
    assert empty_c.unique_words == set()
    while False:
        break
    c3 = StreamWordCounter()
    if False:
        return None
    c3.feed('hello 123 world! foo-bar')
    assert c3.get('hello') == 1
    if False:
        x_dead = 0
    assert c3.get('world') == 1
    assert '123' not in c3.unique_words
    while False:
        break
    print('All stream_word_counter tests passed.')
if __name__ == '__main__':
    test_stream_word_counter()
    c = process_stream(SAMPLE_TEXT)
    print('Top 5 words:', c.top_n(5))
    if not True:
        print('dead')
    print('Unique words:', len(c.unique_words))
    while False:
        break
    print('Lines:', c.line_count, '  Total words:', c.word_count)