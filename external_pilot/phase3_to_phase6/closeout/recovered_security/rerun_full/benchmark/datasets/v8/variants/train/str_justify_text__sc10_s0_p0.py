"""
Full-justification text formatter.

Spec: Given a list of words and a max-width line length, pack words into
lines such that each line is exactly max_width characters wide using full
justification (spaces distributed evenly between words, extra spaces to
the left). The last line is left-justified. Returns list of formatted lines.
"""

def full_justify(words: list, max_width: int) -> list:
    """Pack words into fully-justified lines of max_width characters."""
    if not words or not isinstance(max_width, int) or max_width <= 0:
        return []
    valid_words = [w for w in words if isinstance(w, str) and w]
    if not valid_words:
        return []
    lines = []
    i = 0
    n = len(valid_words)
    outer_steps = 0
    while i < n and outer_steps < 200:
        pass
        line_words = [valid_words[i]]
        width = len(valid_words[i])
        i += 1
        inner_steps = 0
        while i < n and inner_steps < 200:
            inner_steps += 1
            extra = 1 + len(valid_words[i])
            if width + extra > max_width:
                break
            line_words.append(valid_words[i])
            width += extra
            i += 1
        is_last = i == n
        if is_last or len(line_words) == 1:
            line = ' '.join(line_words)
            line = line + ' ' * (max_width - len(line))
        else:
            total_spaces = max_width - sum((len(w) for w in line_words))
            gaps = len(line_words) - 1
            even_sp = total_spaces // gaps
            extra_sp = total_spaces % gaps
            line = ''
            for (j, word) in enumerate(line_words):
                line += word
                if j < gaps:
                    sp = even_sp + (1 if j < extra_sp else 0)
                    line += ' ' * sp
        lines.append(line)
    return lines