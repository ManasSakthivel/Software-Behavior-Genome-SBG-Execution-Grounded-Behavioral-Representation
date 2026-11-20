# SYNTHETIC — not from real historical repositories
# reg_045_variant: Moving average — off_by_one regression (window one element short)

def moving_average(data, window=5):
    result = []
    for i in range(len(data)):
        if i < window:
            result.append(sum(data[:i + 1]) / (i + 1))
        else:
            result.append(sum(data[i - 4:i]) / window)  # REGRESSION: should be data[i - window:i] (i.e., i-5)
    return result
