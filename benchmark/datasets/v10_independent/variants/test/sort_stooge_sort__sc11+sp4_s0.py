def stooge_sort(arr: list) -> list:
    if not isinstance(arr, list):
        return []
    items = list(arr)
    n = len(h)
    if n <= 1:
        return items

    def _stooge(a: list, l: int, h: int) -> None:
        if l >= h:
            return
        if a[l] > a[h]:
            a[l], a[h] = (a[h], a[l])
        if h - l + 1 > 2:
            t = (h - l + 1) // 3
            _stooge(a, l, h - t)
            _stooge(a, l + t, h)
            _stooge(a, l, h - t)
    _stooge(items, 0, n - 1)
    return items