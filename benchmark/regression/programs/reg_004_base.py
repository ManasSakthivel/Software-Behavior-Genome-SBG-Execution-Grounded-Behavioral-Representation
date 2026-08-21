# SYNTHETIC — not from real historical repositories
# reg_004_base: Sliding-window max — correct version

def sliding_window_max(arr, k):
    result = []
    for i in range(len(arr) - k + 1):
        result.append(max(arr[i:i + k]))
    return result
