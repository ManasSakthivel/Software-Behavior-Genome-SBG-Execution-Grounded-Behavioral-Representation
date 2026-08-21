"""
regression_pairs.py — Real-world style regression corpus for SBG V5.

15 function pairs (buggy vs fixed) representing genuine behavioral bugs.
Each pair has: trigger inputs that expose the bug, expected outputs,
and flags indicating whether the bug is visible to exception/volume shortcuts.

Used by: experiments/v5/regression_evaluator.py
"""

# ─────────────────────────────────────────────────────────────────────────────
# REG_01: Binary search off-by-one in boundary initialisation
# ─────────────────────────────────────────────────────────────────────────────

def _reg01_buggy(arr, target):
    lo, hi = 0, len(arr)          # BUG: hi should be len(arr) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if mid >= len(arr):        # out-of-bounds mid → wrong result
            return -1
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def _reg01_fixed(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


# ─────────────────────────────────────────────────────────────────────────────
# REG_02: Missing base case — recursive max on empty list crashes
# ─────────────────────────────────────────────────────────────────────────────

def _reg02_buggy(lst):
    # BUG: no check for empty list — raises IndexError
    if len(lst) == 1:
        return lst[0]
    return max(lst[0], _reg02_buggy(lst[1:]))


def _reg02_fixed(lst):
    if len(lst) == 0:
        return None
    if len(lst) == 1:
        return lst[0]
    return max(lst[0], _reg02_fixed(lst[1:]))


# ─────────────────────────────────────────────────────────────────────────────
# REG_03: Wrong comparison operator — >= instead of > for strict inequality
# ─────────────────────────────────────────────────────────────────────────────

def _reg03_buggy(scores):
    """Return indices of elements strictly greater than threshold 50."""
    threshold = 50
    return [i for i, s in enumerate(scores) if s >= threshold]   # BUG: should be >


def _reg03_fixed(scores):
    threshold = 50
    return [i for i, s in enumerate(scores) if s > threshold]


# ─────────────────────────────────────────────────────────────────────────────
# REG_04: Off-by-one in loop (fencepost error)
# ─────────────────────────────────────────────────────────────────────────────

def _reg04_buggy(n):
    """Return list [0, 1, ..., n] (n+1 elements)."""
    result = []
    for i in range(n):            # BUG: should be range(n + 1)
        result.append(i)
    return result


def _reg04_fixed(n):
    result = []
    for i in range(n + 1):
        result.append(i)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# REG_05: Wrong variable used in computation
# ─────────────────────────────────────────────────────────────────────────────

def _reg05_buggy(a, b):
    """Return (a+b, a*b)."""
    total = a + b
    product = a * a            # BUG: should be a * b
    return total, product


def _reg05_fixed(a, b):
    total = a + b
    product = a * b
    return total, product


# ─────────────────────────────────────────────────────────────────────────────
# REG_06: Missing empty-list guard
# ─────────────────────────────────────────────────────────────────────────────

def _reg06_buggy(lst):
    """Return maximum of list."""
    # BUG: raises ValueError on empty list; should return None
    return max(lst)


def _reg06_fixed(lst):
    if not lst:
        return None
    return max(lst)


# ─────────────────────────────────────────────────────────────────────────────
# REG_07: Integer division truncation
# ─────────────────────────────────────────────────────────────────────────────

def _reg07_buggy(a, b):
    """Return float average."""
    return (a + b) // 2          # BUG: integer division loses fractional part


def _reg07_fixed(a, b):
    return (a + b) / 2


# ─────────────────────────────────────────────────────────────────────────────
# REG_08: Wrong return on one branch (returns None implicitly)
# ─────────────────────────────────────────────────────────────────────────────

def _reg08_buggy(n):
    """Recursive factorial."""
    if n <= 0:
        return 1
    # BUG: missing return keyword — returns None for n > 0
    n * _reg08_buggy(n - 1)


def _reg08_fixed(n):
    if n <= 0:
        return 1
    return n * _reg08_fixed(n - 1)


# ─────────────────────────────────────────────────────────────────────────────
# REG_09: Mutation during iteration (modifies list in-place while iterating)
# ─────────────────────────────────────────────────────────────────────────────

def _reg09_buggy(lst, val):
    """Remove all occurrences of val from lst."""
    for item in lst:             # BUG: mutating lst while iterating → skips elements
        if item == val:
            lst.remove(item)
    return lst


def _reg09_fixed(lst, val):
    return [x for x in lst if x != val]


# ─────────────────────────────────────────────────────────────────────────────
# REG_10: Wrong index access
# ─────────────────────────────────────────────────────────────────────────────

def _reg10_buggy(matrix, row, col):
    """Return element at (row, col) of 2D matrix."""
    return matrix[row][row]      # BUG: second index should be col


def _reg10_fixed(matrix, row, col):
    return matrix[row][col]


# ─────────────────────────────────────────────────────────────────────────────
# REG_11: Missing break — keeps searching after finding answer
# ─────────────────────────────────────────────────────────────────────────────

def _reg11_buggy(lst, target):
    """Return index of first occurrence of target, or -1."""
    result = -1
    for i, val in enumerate(lst):
        if val == target:
            result = i           # BUG: no break, overwrites with last occurrence
    return result


def _reg11_fixed(lst, target):
    for i, val in enumerate(lst):
        if val == target:
            return i
    return -1


# ─────────────────────────────────────────────────────────────────────────────
# REG_12: Mutable default argument (classic Python gotcha)
# ─────────────────────────────────────────────────────────────────────────────

def _reg12_buggy_factory():
    """Returns function with mutable default — accumulates state across calls."""
    def append_item(item, lst=[]):   # BUG: mutable default
        lst.append(item)
        return list(lst)
    return append_item


def _reg12_fixed_factory():
    def append_item(item, lst=None):
        if lst is None:
            lst = []
        lst.append(item)
        return list(lst)
    return append_item


# ─────────────────────────────────────────────────────────────────────────────
# REG_13: Wrong string slicing (drops last char vs first char)
# ─────────────────────────────────────────────────────────────────────────────

def _reg13_buggy(s):
    """Return string with first character removed."""
    return s[:-1]                # BUG: removes last character, not first


def _reg13_fixed(s):
    return s[1:]


# ─────────────────────────────────────────────────────────────────────────────
# REG_14: Sorted in wrong direction
# ─────────────────────────────────────────────────────────────────────────────

def _reg14_buggy(lst):
    """Return list sorted in descending order."""
    return sorted(lst)           # BUG: ascending order, should be descending


def _reg14_fixed(lst):
    return sorted(lst, reverse=True)


# ─────────────────────────────────────────────────────────────────────────────
# REG_15: Recursive Fibonacci with incorrect base case
# ─────────────────────────────────────────────────────────────────────────────

def _reg15_buggy(n):
    """Return nth Fibonacci number (0-indexed: fib(0)=0, fib(1)=1)."""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    if n == 2:                   # BUG: extra case returns wrong value
        return 1
    return _reg15_buggy(n - 1) + _reg15_buggy(n - 2)
    # Note: fib(2) = fib(1) + fib(0) = 1 + 0 = 1, which happens to be correct here;
    # the real bug shows up differently — let's use a version that actually differs
    # Fixed version doesn't have the special case (but result is same).
    # For a real divergence: change the n==2 return to 2:


def _reg15_buggy_v2(n):
    """Fibonacci with wrong base case fib(2)=2 instead of 1."""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    if n == 2:
        return 2                 # BUG: should be 1
    return _reg15_buggy_v2(n - 1) + _reg15_buggy_v2(n - 2)


def _reg15_fixed(n):
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return _reg15_fixed(n - 1) + _reg15_fixed(n - 2)


# ─────────────────────────────────────────────────────────────────────────────
# CORPUS REGISTRY
# ─────────────────────────────────────────────────────────────────────────────

REGRESSION_PAIRS = [
    {
        "id": "REG_01",
        "name": "binary_search_off_by_one",
        "description": "hi initialised to len(arr) instead of len(arr)-1; accesses arr[len(arr)] → IndexError",
        "bug_type": "off_by_one",
        "buggy_fn": _reg01_buggy,
        "fixed_fn": _reg01_fixed,
        "trigger_inputs": [([1, 3, 5, 7, 9], 9), ([2, 4, 6, 8], 6), ([1], 1)],
        "bug_visible_to_exception": True,   # raises IndexError
        "bug_visible_to_volume": False,
    },
    {
        "id": "REG_02",
        "name": "missing_base_case_empty_list",
        "description": "No guard for empty list; _reg02_buggy([]) raises IndexError",
        "bug_type": "missing_edge_case",
        "buggy_fn": _reg02_buggy,
        "fixed_fn": _reg02_fixed,
        "trigger_inputs": [([], ), ([3, 1, 4], )],
        "bug_visible_to_exception": True,
        "bug_visible_to_volume": False,
    },
    {
        "id": "REG_03",
        "name": "wrong_comparison_operator",
        "description": ">= instead of > — includes the threshold value when it shouldn't",
        "bug_type": "wrong_operator",
        "buggy_fn": _reg03_buggy,
        "fixed_fn": _reg03_fixed,
        "trigger_inputs": [([40, 50, 60], ), ([50, 51], )],
        "bug_visible_to_exception": False,
        "bug_visible_to_volume": False,
    },
    {
        "id": "REG_04",
        "name": "loop_fencepost_error",
        "description": "range(n) instead of range(n+1) — missing the last element",
        "bug_type": "off_by_one",
        "buggy_fn": _reg04_buggy,
        "fixed_fn": _reg04_fixed,
        "trigger_inputs": [(3, ), (0, ), (5, )],
        "bug_visible_to_exception": False,
        "bug_visible_to_volume": True,   # loop runs N-1 iterations
    },
    {
        "id": "REG_05",
        "name": "wrong_variable_in_product",
        "description": "a*a instead of a*b — uses wrong variable in product computation",
        "bug_type": "wrong_variable",
        "buggy_fn": _reg05_buggy,
        "fixed_fn": _reg05_fixed,
        "trigger_inputs": [(2, 3), (4, 5), (1, 7)],
        "bug_visible_to_exception": False,
        "bug_visible_to_volume": False,
    },
    {
        "id": "REG_06",
        "name": "missing_empty_guard",
        "description": "max() on empty list raises ValueError",
        "bug_type": "missing_edge_case",
        "buggy_fn": _reg06_buggy,
        "fixed_fn": _reg06_fixed,
        "trigger_inputs": [([], ), ([3, 1, 4, 1, 5], )],
        "bug_visible_to_exception": True,
        "bug_visible_to_volume": False,
    },
    {
        "id": "REG_07",
        "name": "integer_division_truncation",
        "description": "// instead of / — truncates fractional average",
        "bug_type": "wrong_operator",
        "buggy_fn": _reg07_buggy,
        "fixed_fn": _reg07_fixed,
        "trigger_inputs": [(3, 4), (1, 2), (7, 8)],
        "bug_visible_to_exception": False,
        "bug_visible_to_volume": False,
    },
    {
        "id": "REG_08",
        "name": "missing_return_keyword",
        "description": "Missing 'return' — recursive calls return None for n > 0",
        "bug_type": "missing_return",
        "buggy_fn": _reg08_buggy,
        "fixed_fn": _reg08_fixed,
        "trigger_inputs": [(3, ), (5, ), (1, )],
        "bug_visible_to_exception": False,
        "bug_visible_to_volume": False,
    },
    {
        "id": "REG_09",
        "name": "mutation_during_iteration",
        "description": "Removes from list while iterating — skips duplicate elements",
        "bug_type": "mutation_during_iteration",
        "buggy_fn": _reg09_buggy,
        "fixed_fn": _reg09_fixed,
        "trigger_inputs": [([1, 2, 2, 3], 2), ([1, 1, 1], 1), ([1, 2, 3], 2)],
        "bug_visible_to_exception": False,
        "bug_visible_to_volume": True,   # different iterations
    },
    {
        "id": "REG_10",
        "name": "wrong_index_access",
        "description": "matrix[row][row] instead of matrix[row][col] — uses row twice",
        "bug_type": "wrong_variable",
        "buggy_fn": _reg10_buggy,
        "fixed_fn": _reg10_fixed,
        "trigger_inputs": [([[1, 2], [3, 4]], 0, 1), ([[5, 6, 7], [8, 9, 10]], 1, 2)],
        "bug_visible_to_exception": False,
        "bug_visible_to_volume": False,
    },
    {
        "id": "REG_11",
        "name": "missing_break_finds_last",
        "description": "No break after finding target — returns last occurrence instead of first",
        "bug_type": "missing_break",
        "buggy_fn": _reg11_buggy,
        "fixed_fn": _reg11_fixed,
        "trigger_inputs": [([1, 2, 3, 2, 1], 2), ([4, 5, 6], 5), ([1, 1, 1], 1)],
        "bug_visible_to_exception": False,
        "bug_visible_to_volume": True,   # buggy runs full loop, fixed exits early
    },
    {
        "id": "REG_12",
        "name": "mutable_default_argument",
        "description": "Mutable default list accumulates state across calls",
        "bug_type": "mutable_default",
        "buggy_fn": _reg12_buggy_factory(),
        "fixed_fn": _reg12_fixed_factory(),
        "trigger_inputs": [(1, ), (2, ), (3, )],   # called sequentially, state accumulates
        "bug_visible_to_exception": False,
        "bug_visible_to_volume": False,
    },
    {
        "id": "REG_13",
        "name": "wrong_string_slicing",
        "description": "s[:-1] removes last char; should be s[1:] to remove first char",
        "bug_type": "wrong_slice",
        "buggy_fn": _reg13_buggy,
        "fixed_fn": _reg13_fixed,
        "trigger_inputs": [("hello", ), ("abc", ), ("xy", )],
        "bug_visible_to_exception": False,
        "bug_visible_to_volume": False,
    },
    {
        "id": "REG_14",
        "name": "wrong_sort_direction",
        "description": "sorted(lst) returns ascending; should be descending",
        "bug_type": "wrong_operator",
        "buggy_fn": _reg14_buggy,
        "fixed_fn": _reg14_fixed,
        "trigger_inputs": [([3, 1, 4, 1, 5], ), ([10, 2, 7], ), ([1, 2], )],
        "bug_visible_to_exception": False,
        "bug_visible_to_volume": False,
    },
    {
        "id": "REG_15",
        "name": "fibonacci_wrong_base_case",
        "description": "fib(2) returns 2 instead of 1 — wrong base case causes cascade",
        "bug_type": "wrong_base_case",
        "buggy_fn": _reg15_buggy_v2,
        "fixed_fn": _reg15_fixed,
        "trigger_inputs": [(2, ), (4, ), (6, )],
        "bug_visible_to_exception": False,
        "bug_visible_to_volume": False,
    },
]


if __name__ == "__main__":
    print(f"Regression corpus: {len(REGRESSION_PAIRS)} pairs")
    errors = 0
    for pair in REGRESSION_PAIRS:
        print(f"\n  {pair['id']}: {pair['name']}")
        for inp in pair["trigger_inputs"][:2]:
            try:
                buggy_out = pair["buggy_fn"](*inp)
            except Exception as e:
                buggy_out = f"ERROR:{type(e).__name__}"
            try:
                fixed_out = pair["fixed_fn"](*inp)
            except Exception as e:
                fixed_out = f"ERROR:{type(e).__name__}"
            diverges = buggy_out != fixed_out
            status = "✓ DIVERGES" if diverges else "✗ SAME"
            print(f"    input={inp} buggy={buggy_out} fixed={fixed_out} [{status}]")
            if not diverges:
                errors += 1
    print(f"\nTotal divergence failures (expected 0 or few): {errors}")
