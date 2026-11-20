# SYNTHETIC — not from real historical repositories
# reg_004_variant: Sliding-window max — off_by_one regression (last window skipped)

def sliding_window_max(arr, k):
    result = []
    for i in range(len(arr) - k):  # REGRESSION: should be len(arr) - k + 1
        result.append(max(arr[i:i + k]))
    return result
