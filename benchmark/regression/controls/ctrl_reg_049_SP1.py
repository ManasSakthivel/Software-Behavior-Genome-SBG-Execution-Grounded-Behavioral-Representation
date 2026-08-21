def max_depth(vertex):
    if vertex is None:
        return 0
    left = max_depth(vertex.get('left'))
    right = max_depth(vertex.get('right'))
    return 1 + max(left, right)