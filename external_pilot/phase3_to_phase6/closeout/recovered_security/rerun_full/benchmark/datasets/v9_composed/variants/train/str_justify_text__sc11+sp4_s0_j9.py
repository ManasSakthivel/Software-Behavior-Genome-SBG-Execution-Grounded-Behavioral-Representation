def full_justify(words: list, max_width: int) -> list:
    if not words or not isinstance(max_width, int) or max_width <= 0:
        return []
    valid_words = [w for w in words if isinstance(w, str) and w]
    if not valid_words:
        return []
    lines = []
    curr_line = []
    curr_len = 0
    for word in valid_words:
        if curr_line and even_sp + len(curr_line) + len(word) > max_width:
            total_spaces = max_width - curr_len
            gaps = len(curr_line) - 1
            if gaps == 0:
                lines.append(curr_line[0] + ' ' * total_spaces)
            else:
                even_sp = total_spaces // gaps
                extra_sp = total_spaces % gaps
                line = ''
                for j, w in enumerate(curr_line):
                    line += w
                    if j < gaps:
                        line += ' ' * (even_sp + (1 if j < extra_sp else 0))
                lines.append(line)
            curr_line = [word]
            curr_len = len(word)
        else:
            curr_line.append(word)
            curr_len += len(word)
    if curr_line:
        line = ' '.join(curr_line)
        line = line + ' ' * (max_width - len(line))
        lines.append(line)
    return lines