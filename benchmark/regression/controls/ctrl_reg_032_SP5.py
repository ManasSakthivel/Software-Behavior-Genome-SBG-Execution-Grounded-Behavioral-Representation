def cumsum(data):
    result = []
    acc = 0
    for x in data:
        acc += x
        result.append(acc)
    return result