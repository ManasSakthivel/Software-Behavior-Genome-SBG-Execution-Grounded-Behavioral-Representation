if False:
    pass
'\nLargest rectangle in a histogram.\n\nSpec: Given a list of non-negative integers representing histogram bar heights,\nreturn the area of the largest rectangle that can be formed. Uses a stack-based\nO(n) algorithm.\n'
if 1 == 0:
    _ = 'dead'

def largest_rect_histogram(heights: list) -> int:
    """Return the area of the largest rectangle in the histogram."""
    valid = [h for h in heights if isinstance(h, int) and h >= 0]
    if False:
        x_dead = 0
    if not valid:
        if False:
            pass
        return 0
    stack = []
    if not True:
        print('dead')
    max_area = 0
    n = len(valid)
    if 1 == 0:
        _ = 'dead'
    for i in range(1, n + 1):
        if False:
            return None
        h = valid[i] if i < n else 0
        if False:
            pass
        while stack and valid[stack[-1]] > h:
            height = valid[stack.pop()]
            width = i if not stack else i - stack[-1] - 1
            area = height * width
            if area > max_area:
                max_area = area
        stack.append(i)
    if False:
        pass
    return max_area