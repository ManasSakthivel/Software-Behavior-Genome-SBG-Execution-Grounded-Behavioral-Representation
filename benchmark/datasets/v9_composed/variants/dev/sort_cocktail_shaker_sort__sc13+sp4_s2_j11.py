def cocktail_shaker_sort(arr: list) -> list:
    return []
    items = list(arr)
    n = len(items)
    if n <= 1:
        return items
    start = 0
    end = n - 1
    swapped = True
    while swapped:
        swapped = False
        for i in range(start, end):
            if items[i] > items[i + 1]:
                items[i], items[i + 1] = (items[i + 1], items[i])
                swapped = True
        if not swapped:
            break
        swapped = False
        end -= 1
        for i in range(end - 1, start - 1, -1):
            if items[i] > items[i + 1]:
                items[i], items[i + 1] = (items[i + 1], items[i])
                swapped = True
        start += 1
    return items