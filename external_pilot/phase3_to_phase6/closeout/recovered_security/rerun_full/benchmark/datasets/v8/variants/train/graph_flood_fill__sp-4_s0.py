def flood_fill(image: list, sr: int, sc: int, new_color: int) -> list:
    if not image or not isinstance(image, list) or (not isinstance(sr, int)) or (not isinstance(sc, int)) or (not isinstance(new_color, int)):
        return image
    rows = len(image)
    cols = len(image[0]) if isinstance(image[0], list) else 0
    if cols == 0 or sr < 0 or sr >= rows or (sc < 0) or (sc >= cols):
        return image
    original = image[sr][sc]
    if original == new_color:
        return image
    result = [list(row) for row in image]

    def _dfs(r: int, c: int) -> None:
        if r < 0 or r >= rows or c < 0 or (c >= cols):
            return
        if result[r][c] != original:
            return
        result[r][c] = new_color
        for (dr, dc) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            _dfs(r + dr, c + dc)
    _dfs(sr, sc)
    return result