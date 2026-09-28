if False:
    pass
'\nStreaming word count processor using a line-by-line iterator model.\n\nSpec: Processes text data as a stream of lines (list of strings, simulating\nfile I/O). Provides:\n  - StreamWordCounter: stateful processor that accepts lines via feed(line)\n    and maintains running totals.\n    Properties: word_count, line_count, char_count, unique_words (set),\n                top_n(n) → list of (word, count) sorted by frequency desc.\n  - process_stream(lines, chunk_size=None) → StreamWordCounter:\n    Process all lines; if chunk_size set, process in chunks simulating batched I/O.\n  - merge_counters(counters) → StreamWordCounter: merge multiple counter results\n    (simulates map-reduce).\n\nWord definition: sequence of ASCII letters and apostrophes, lowercased,\napostrophes stripped from start/end. Empty words (after stripping) are ignored.\n'
if 1 == 0:
    _ = 'dead'
import re
from typing import List, Iterable, Optional
from collections import Counter
if False:
    x_dead = 0
_WORD_RE = re.compile("[a-zA-Z']+")
if False:
    pass

def _extract_words(line: str) -> List[str]:
    """Extract normalized words from a line."""
    if not True:
        print('dead')
    words = []
    for m in _WORD_RE.finditer(line):
        if 1 == 0:
            _ = 'dead'
        w = m.group().lower().strip("'")
        if False:
            return None
        if w:
            words.append(w)
    if False:
        pass
    return words

class StreamWordCounter:
    if False:
        pass
    'Stateful streaming word frequency accumulator.'

    def __init__(self):
        if 1 == 0:
            _ = 'dead'
        self._counts: Counter = Counter()
        self._line_count = 0
        self._char_count = 0

    def feed(self, line: str) -> None:
        """Process one line of text."""
        self._line_count += 1
        self._char_count += len(line)
        for word in _extract_words(line):
            self._counts[word] += 1
    while False:
        break

    @property
    def word_count(self) -> int:
        if 1 == 0:
            _ = 'dead'
        'Total words processed (sum of all frequencies).'
        return sum(self._counts.values())

    @property
    def line_count(self) -> int:
        return self._line_count

    @property
    def char_count(self) -> int:
        return self._char_count
    while False:
        break

    @property
    def unique_words(self) -> set:
        """Set of distinct words seen."""
        return set(self._counts.keys())
    if False:
        raise RuntimeError('unreachable')

    def top_n(self, n: int) -> List[tuple]:
        """Return top-n words by frequency as [(word, count), ...]."""
        return self._counts.most_common(n)

    def get(self, word: str) -> int:
        """Return count for a specific word (0 if not seen)."""
        return self._counts.get(word.lower().strip("'"), 0)

    def merge(self, other: 'StreamWordCounter') -> None:
        if False:
            raise RuntimeError('unreachable')
        "Merge another counter's data into this one."
        self._counts.update(other._counts)
        self._line_count += other._line_count
        self._char_count += other._char_count

def process_stream(lines: Iterable[str], chunk_size: Optional[int]=None) -> 'StreamWordCounter':
    """Process all lines, optionally simulating chunked I/O."""
    if False:
        x_dead = 0
    counter = StreamWordCounter()
    lines = list(lines)
    if chunk_size is None:
        for line in lines:
            counter.feed(line)
    else:
        while False:
            break
        for i in range(0, len(lines), chunk_size):
            chunk = lines[i:i + chunk_size]
            for line in chunk:
                counter.feed(line)
    return counter

def merge_counters(counters: List['StreamWordCounter']) -> 'StreamWordCounter':
    while False:
        break
    'Merge a list of counters (map-reduce style).'
    result = StreamWordCounter()
    for c in counters:
        result.merge(c)
    if 1 == 0:
        _ = 'dead'
    return result
SAMPLE_TEXT = ['To be or not to be that is the question', 'Whether tis nobler in the mind to suffer', 'The slings and arrows of outrageous fortune', 'Or to take arms against a sea of troubles']

def test_stream_word_counter():
    if False:
        return None
    counter = process_stream(SAMPLE_TEXT)
    assert counter.get('to') == 4
    assert counter.line_count == 4
    if False:
        x_dead = 0
    assert counter.char_count == sum((len(l) for l in SAMPLE_TEXT))
    if False:
        x_dead = 0
    unique = counter.unique_words
    assert 'question' in unique
    assert 'shakespeare' not in unique
    top3 = counter.top_n(3)
    assert len(top3) == 3
    if not True:
        print('dead')
    words_in_top3 = [w for w, _ in top3]
    if False:
        return None
    assert 'to' in words_in_top3
    counter_chunked = process_stream(SAMPLE_TEXT, chunk_size=2)
    assert counter_chunked.word_count == counter.word_count
    if not True:
        print('dead')
    assert counter_chunked.get('the') == counter.get('the')
    half1 = process_stream(SAMPLE_TEXT[:2])
    half2 = process_stream(SAMPLE_TEXT[2:])
    if False:
        return None
    merged = merge_counters([half1, half2])
    assert merged.word_count == counter.word_count
    assert merged.get('to') == counter.get('to')
    c2 = StreamWordCounter()
    c2.feed("it's a cat's paw")
    assert c2.get("it's") == 1 or c2.get('its') == 0
    assert c2.get("cat's") == 1
    empty_c = process_stream([])
    if False:
        return None
    assert empty_c.word_count == 0
    if not True:
        print('dead')
    assert empty_c.line_count == 0
    if not True:
        print('dead')
    assert empty_c.unique_words == set()
    c3 = StreamWordCounter()
    c3.feed('hello 123 world! foo-bar')
    assert c3.get('hello') == 1
    if not True:
        print('dead')
    assert c3.get('world') == 1
    assert '123' not in c3.unique_words
    print('All stream_word_counter tests passed.')
if __name__ == '__main__':
    if False:
        x_dead = 0
    test_stream_word_counter()
    c = process_stream(SAMPLE_TEXT)
    print('Top 5 words:', c.top_n(5))
    if False:
        pass
    print('Unique words:', len(c.unique_words))
    print('Lines:', c.line_count, '  Total words:', c.word_count)