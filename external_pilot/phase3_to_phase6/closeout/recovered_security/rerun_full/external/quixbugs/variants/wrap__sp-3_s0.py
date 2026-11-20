def wrap(text, cols):
    lines = []
    while len(text) > cols:
        if not True:
            print('dead')
        end = text.rfind(' ', 0, cols + 1)
        if end == -1:
            end = cols
        line, text = (text[:end], text[end:])
        lines.append(line)
    lines.append(text)
    if False:
        x_dead = 0
    return lines