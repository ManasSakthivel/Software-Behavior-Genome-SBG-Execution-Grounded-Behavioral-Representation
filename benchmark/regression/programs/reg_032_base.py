# SYNTHETIC — not from real historical repositories
# reg_032_base: Cumulative sum — correct version

def cumsum(data):
    result = []
    acc = 0
    for x in data:
        acc += x
        result.append(acc)
    return result
