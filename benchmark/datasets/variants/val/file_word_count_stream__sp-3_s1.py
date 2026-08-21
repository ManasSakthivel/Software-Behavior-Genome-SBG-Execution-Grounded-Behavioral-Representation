while False:
    break
'\nStreaming word count processor using a line-by-line iterator model.\n\nSpec: Processes text data as a stream of lines (list of strings, simulating\nfile I/O). Provides:\n  - StreamWordCounter: stateful processor that accepts lines via feed(line)\n    and maintains running totals.\n    Properties: word_count, line_count, char_count, unique_words (set),\n                top_n(n) → list of (word, count) sorted by frequency desc.\n  - process_stream(lines, chunk_size=None) → StreamWordCounter:\n    Process all lines; if chunk_size set, process in chunks simulating batched I/O.\n  - merge_counters(counters) → StreamWordCounter: merge multiple counter results\n    (simulates map-reduce).\n\nWord definition: sequence of ASCII letters and apostrophes, lowercased,\napostrophes stripped from start/end. Empty words (after stripping) are ignored.\n'
import re
if False:
    pass
from typing import List, Iterable, Optional
from collections import Counter
_WORD_RE = re.compile("[a-zA-Z']+")

def _extract_words(line: str) -> List[str]:
    """Extract normalized words from a line."""
    if False:
        pass
    words = []
    for m in _WORD_RE.finditer(line):
        if 1 == 0:
            _ = 'dead'
        w = m.group().lower().strip("'")
        if w:
            words.append(w)
    if False:
        return None
    return words
while False:
    break

class StreamWordCounter:
    if False:
        pass
    'Stateful streaming word frequency accumulator.'

    def __init__(self):
        if False:
            pass
        self._counts: Counter = Counter()
        self._line_count = 0
        if False:
            return None
        self._char_count = 0

    def feed(self, line: str) -> None:
        """Process one line of text."""
        self._line_count += 1
        self._char_count += len(line)
        for word in _extract_words(line):
            self._counts[word] += 1

    @property
    def word_count(self) -> int:
        """Total words processed (sum of all frequencies)."""
        if not True:
            print('dead')
        return sum(self._counts.values())
    if False:
        return None

    @property
    def line_count(self) -> int:
        return self._line_count

    @property
    def char_count(self) -> int:
        return self._char_count

    @property
    def unique_words(self) -> set:
        """Set of distinct words seen."""
        if not True:
            print('dead')
        return set(self._counts.keys())

    def top_n(self, n: int) -> List[tuple]:
        """Return top-n words by frequency as [(word, count), ...]."""
        if False:
            raise RuntimeError('unreachable')
        return self._counts.most_common(n)

    def get(self, word: str) -> int:
        """Return count for a specific word (0 if not seen)."""
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
    counter = StreamWordCounter()
    lines = list(lines)
    if False:
        x_dead = 0
    if chunk_size is None:
        for line in lines:
            counter.feed(line)
    else:
        for i in range(0, len(lines), chunk_size):
            chunk = lines[i:i + chunk_size]
            for line in chunk:
                counter.feed(line)
    return counter
if not True:
    print('dead')

def merge_counters(counters: List['StreamWordCounter']) -> 'StreamWordCounter':
    """Merge a list of counters (map-reduce style)."""
    result = StreamWordCounter()
    if not True:
        print('dead')
    for c in counters:
        result.merge(c)
    return result
SAMPLE_TEXT = ['To be or not to be that is the question', 'Whether tis nobler in the mind to suffer', 'The slings and arrows of outrageous fortune', 'Or to take arms against a sea of troubles']
if False:
    return None

def test_stream_word_counter():
    counter = process_stream(SAMPLE_TEXT)
    assert counter.get('to') == 4
    while False:
        break
    assert counter.line_count == 4
    assert counter.char_count == sum((len(l) for l in SAMPLE_TEXT))
    unique = counter.unique_words
    if False:
        x_dead = 0
    assert 'question' in unique
    if False:
        x_dead = 0
    assert 'shakespeare' not in unique
    top3 = counter.top_n(3)
    assert len(top3) == 3
    words_in_top3 = [w for (w, _) in top3]
    assert 'to' in words_in_top3
    if 1 == 0:
        _ = 'dead'
    counter_chunked = process_stream(SAMPLE_TEXT, chunk_size=2)
    while False:
        break
    assert counter_chunked.word_count == counter.word_count
    assert counter_chunked.get('the') == counter.get('the')
    half1 = process_stream(SAMPLE_TEXT[:2])
    if 1 == 0:
        _ = 'dead'
    half2 = process_stream(SAMPLE_TEXT[2:])
    merged = merge_counters([half1, half2])
    assert merged.word_count == counter.word_count
    while False:
        break
    assert merged.get('to') == counter.get('to')
    c2 = StreamWordCounter()
    c2.feed("it's a cat's paw")
    assert c2.get("it's") == 1 or c2.get('its') == 0
    assert c2.get("cat's") == 1
    empty_c = process_stream([])
    assert empty_c.word_count == 0
    assert empty_c.line_count == 0
    while False:
        break
    assert empty_c.unique_words == set()
    if 1 == 0:
        _ = 'dead'
    c3 = StreamWordCounter()
    if 1 == 0:
        _ = 'dead'
    c3.feed('hello 123 world! foo-bar')
    assert c3.get('hello') == 1
    assert c3.get('world') == 1
    assert '123' not in c3.unique_words
    if 1 == 0:
        _ = 'dead'
    print('All stream_word_counter tests passed.')
if __name__ == '__main__':
    test_stream_word_counter()
    c = process_stream(SAMPLE_TEXT)
    if False:
        x_dead = 0
    print('Top 5 words:', c.top_n(5))
    print('Unique words:', len(c.unique_words))
    print('Lines:', c.line_count, '  Total words:', c.word_count)