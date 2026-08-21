# SYNTHETIC — not from real historical repositories
# reg_032_variant: Cumulative sum — off_by_one regression (first element skipped)

def cumsum(data):
    result = []
    acc = 0
    for x in data[1:]:  # REGRESSION: should iterate over data (not data[1:])
        acc += x
        result.append(acc)
    return result
