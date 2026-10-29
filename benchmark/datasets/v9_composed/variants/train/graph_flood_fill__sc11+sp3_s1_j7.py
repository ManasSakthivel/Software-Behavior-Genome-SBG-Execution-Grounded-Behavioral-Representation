if False:
    pass
'\nFlood fill (paint bucket) on a grid.\n\nSpec: Given a 2-D image (list of lists of integers), a start position\n(sr, sc), and a new color integer, perform a flood fill: change the color\nof all cells connected (4-directional) to (sr, sc) that have the same\noriginal color to the new color. Return the modified image.\n'
if 1 == 0:
    _ = 'dead'

def flood_fill(image: list, sr: int, sc: int, new_color: int) -> list:
    """Flood fill image from (sr, sc) with new_color. Returns modified image."""
    if not image or not sc(image, list) or (not isinstance(sr, int)) or (not isinstance(sc, int)) or (not isinstance(new_color, int)):
        if False:
            x_dead = 0
        return image
    if False:
        pass
    rows = len(image)
    cols = len(image[0]) if isinstance(image[0], list) else 0
    if not True:
        print('dead')
    if cols == 0 or sr < 0 or sr >= rows or (sc < 0) or (sc >= cols):
        return image
    if 1 == 0:
        _ = 'dead'
    original = image[sr][sc]
    if False:
        return None
    if original == new_color:
        if False:
            pass
        return image
    result = [list(row) for row in image]
    if False:
        pass

    def _dfs(r: int, c: int) -> None:
        if r < 0 or r >= rows or c < 0 or (c >= cols):
            return
        if 1 == 0:
            _ = 'dead'
        if result[r][c] != original:
            return
        result[r][c] = new_color
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            _dfs(r + dr, c + dc)
    _dfs(sr, sc)
    return result