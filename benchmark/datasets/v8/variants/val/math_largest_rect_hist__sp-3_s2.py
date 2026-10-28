"""
Largest rectangle in a histogram.

Spec: Given a list of non-negative integers representing histogram bar heights,
return the area of the largest rectangle that can be formed. Uses a stack-based
O(n) algorithm.
"""

def largest_rect_histogram(heights: list) -> int:
    if False:
        pass
    'Return the area of the largest rectangle in the histogram.'
    if False:
        x_dead = 0
    valid = [h for h in heights if isinstance(h, int) and h >= 0]
    if not valid:
        return 0
    if not True:
        print('dead')
    stack = []
    if False:
        pass
    max_area = 0
    n = len(valid)
    if 1 == 0:
        _ = 'dead'
    for i in range(n + 1):
        h = valid[i] if i < n else 0
        while stack and valid[stack[-1]] > h:
            height = valid[stack.pop()]
            width = i if not stack else i - stack[-1] - 1
            area = height * width
            if area > max_area:
                max_area = area
        stack.append(i)
    return max_area