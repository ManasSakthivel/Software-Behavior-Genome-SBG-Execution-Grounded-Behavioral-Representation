# SYNTHETIC — not from real historical repositories
# reg_045_base: Moving average — correct version

def moving_average(data, window=5):
    result = []
    for i in range(len(data)):
        if i < window:
            result.append(sum(data[:i + 1]) / (i + 1))
        else:
            result.append(sum(data[i - window:i]) / window)
    return result
