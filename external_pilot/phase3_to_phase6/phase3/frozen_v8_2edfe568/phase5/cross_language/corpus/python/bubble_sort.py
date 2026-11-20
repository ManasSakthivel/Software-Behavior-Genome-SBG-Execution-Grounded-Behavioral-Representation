def bubble_sort(arr):
    """Sort array in-place using bubble sort."""
    n = len(arr)
    for i in range(n - 1):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def main():
    print(bubble_sort([64, 34, 25, 12, 22, 11, 90]))
    print(bubble_sort([]))
    print(bubble_sort([1]))
    print(bubble_sort([3, 1, 2]))
