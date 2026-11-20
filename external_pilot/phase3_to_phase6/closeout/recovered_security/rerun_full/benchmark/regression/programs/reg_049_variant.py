# SYNTHETIC — not from real historical repositories
# reg_049_variant: Tree max depth — wrong_return regression (missing +1, depth off by one)

def max_depth(node):
    if node is None:
        return 0
    left = max_depth(node.get('left'))
    right = max_depth(node.get('right'))
    return max(left, right)  # REGRESSION: should be 1 + max(left, right)
