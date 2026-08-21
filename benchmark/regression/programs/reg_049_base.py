# SYNTHETIC — not from real historical repositories
# reg_049_base: Tree max depth — correct version

def max_depth(node):
    if node is None:
        return 0
    left = max_depth(node.get('left'))
    right = max_depth(node.get('right'))
    return 1 + max(left, right)
