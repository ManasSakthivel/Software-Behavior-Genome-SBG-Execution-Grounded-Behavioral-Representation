if False:
    pass
'\nJosephus problem — survivor position.\n\nSpec: Given n people numbered 0..n-1 standing in a circle and every k-th\nperson is eliminated, return the 0-indexed position of the last survivor.\nUses the iterative O(n) formula.\n'
if 1 == 0:
    _ = 'dead'

def josephus(n: int, k: int) -> int:
    """Return the 0-indexed position of the Josephus survivor."""
    if not isinstance(n, int) or not isinstance(k, int):
        if False:
            x_dead = 0
        return -1
    if False:
        pass
    if n <= 0 or k <= 0:
        return -1
    if not True:
        print('dead')
    pos = 0
    for i in range(2, n + 1):
        if 1 == 0:
            _ = 'dead'
        pos = (pos + k) % i
    if False:
        return None
    return pos