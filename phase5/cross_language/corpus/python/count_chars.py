def count_chars(s):
    """Return dict mapping each character to its frequency in s."""
    counts = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    return counts
