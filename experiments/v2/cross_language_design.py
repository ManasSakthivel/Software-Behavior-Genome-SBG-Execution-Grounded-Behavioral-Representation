"""
experiments/v2/cross_language_design.py
=========================================
H11 Cross-Language Experiment Design — Agent G

Hypothesis (pre-registered in docs/v2/HYPOTHESES_V2.md):
    H11: Hybrid genomes identify equivalent behavior across Python and Java.
    Formal statement: AUROC(cross_language, test) > 0.6
    Power note: N=15 gives ~25% power at α_corrected=0.0042.
    H11 is EXPLORATORY regardless of result — explicitly underpowered by design.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INFRASTRUCTURE AUDIT (honest assessment)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SandboxRunner (sbg/v2/execution/runner.py) wraps the v1 Python Tracer
(sbg.extraction.dynamic.tracer.Tracer). It accepts a Python *callable*
and a list of Python inputs. It returns ExecutionTrace objects built
from Python's sys.settrace mechanism.

Java execution is NOT supported:
  - No javac / JVM subprocess wrapper exists in runner.py
  - No Java AST parser exists in sbg/v2/
  - The v1 Tracer is Python-specific (sys.settrace)
  - DynamicGenome features (coverage_size, anon_call_freq, call_depth_mean,
    hot_path_hash) are all derived from Python traces

Consequence for H11:
  Full Python↔Java behavioral comparison via DynamicGenome is INFEASIBLE
  without Java execution infrastructure. This design document DOES NOT
  fabricate Java execution results.

Alternative achievable:
  Python-to-Python behavioral comparison using the same behavioral
  specification. This tests whether structurally diverse Python
  implementations of the same spec produce similar DynamicGenomes —
  a necessary precondition for cross-language generalization.

  If Python-A and Python-B (different implementations, same spec) already
  fail to match via DynamicGenome, then Python↔Java would certainly fail.
  This is a valid lower-bound diagnostic.

VERDICT: H11 = INSUFFICIENT_EVIDENCE (infrastructure constraint, not
         a negative result). Java evaluation is future work.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXISTING EVIDENCE (Phase 4 E9 + Phase 5 cross_language_results.json)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase 4 E9:
  - N=5 illustrative pairs (Python-only, different idioms, NOT true cross-language)
  - Status: PRELIMINARY_ONLY — results explicitly excluded from quantitative claims
  - Key finding: token/AST-seq features collapse across idiomatic boundaries

Phase 5 cross_language_results.json:
  - N=15 pairs (10 EQUIVALENT, 4 CHANGED; 1 label conflict in data — see notes)
  - Method: normalized control-flow features from regex heuristics on Java source
  - AUROC: 0.4091 (below 0.5 — inversion present)
  - Inversion: EQUIV_mean=0.7479, CHANGED_mean=0.7759 (CHANGED looks MORE similar)
  - Limitation: Java features extracted via regex heuristics, NOT a Java AST parser
  - Verdict (stored): NOT_SUPPORTED

The Phase 5 AUROC of 0.4091 on N=15 pairs with regex-heuristic Java features
cannot be interpreted as a valid H11 test because:
  1. Java features are not execution-derived (no Java executor)
  2. N=15 gives ~25% power — AUROC CI spans the entire [0,1] range
  3. Regex heuristics misclassify recursion flags (see data: changed pairs
     erroneously share has_recursion=True with equivalent pairs)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DESIGN: N=12 PYTHON BEHAVIORAL SPECIFICATION PAIRS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Each pair: (Python-impl-A, Python-impl-B, label, Java_equivalent_spec_note)
  - Both implementations satisfy the SAME behavioral specification
  - Inputs are IDENTICAL for both implementations
  - Expected outputs are IDENTICAL for both implementations
  - Python-impl-B is written in a Java-idiomatic style where possible

This is NOT full Python↔Java comparison. It is:
  "Can DynamicGenome recognize that two Python implementations of the
   same spec are behaviorally equivalent, even when one mimics Java style?"

If yes: provides supporting evidence for cross-language generalizability
        (necessary but not sufficient condition)
If no:  H11 faces an additional challenge beyond infrastructure

N=12 is below the pre-registered N=15 target for H11, but given that full
H11 evaluation is infeasible (no Java executor), this design documents
the maximum achievable scope honestly.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# BEHAVIORAL SPECIFICATION PAIRS (N=12)
# Format: id, category, spec, inputs, expected_outputs,
#         python_idiomatic (impl A), java_style (impl B),
#         changed_variant (impl C — semantically different),
#         java_equivalent_note
# ---------------------------------------------------------------------------

CROSS_LANGUAGE_PAIRS: list[dict] = [
    # ── SORTING ──────────────────────────────────────────────────────────────
    {
        "id": "cl_sort_01_bubble",
        "category": "sorting",
        "spec": "Sort list of integers in ascending order (in-place, return sorted list). "
                "Java equivalent: Arrays.sort() or manual bubble sort.",
        "inputs": [[5, 3, 1, 4, 2], [1], [], [3, 3, 1], [-1, 0, 1]],
        "expected_outputs": [[1, 2, 3, 4, 5], [1], [], [1, 3, 3], [-1, 0, 1]],
        "label": "EQUIVALENT",
        "python_idiomatic": (
            "def bubble_sort(arr):\n"
            "    a = list(arr)\n"
            "    for i in range(len(a) - 1):\n"
            "        for j in range(len(a) - 1 - i):\n"
            "            if a[j] > a[j + 1]:\n"
            "                a[j], a[j + 1] = a[j + 1], a[j]\n"
            "    return a\n"
        ),
        "java_style": (
            "def bubble_sort(arr):\n"
            "    # Java-style: explicit temp variable, index-based swap\n"
            "    a = list(arr)\n"
            "    n = len(a)\n"
            "    i = 0\n"
            "    while i < n - 1:\n"
            "        j = 0\n"
            "        while j < n - 1 - i:\n"
            "            if a[j] > a[j + 1]:\n"
            "                temp = a[j]\n"
            "                a[j] = a[j + 1]\n"
            "                a[j + 1] = temp\n"
            "            j += 1\n"
            "        i += 1\n"
            "    return a\n"
        ),
        "java_equivalent_note": (
            "Java: static int[] bubbleSort(int[] arr) — "
            "identical loop structure to java_style impl above. "
            "Control-flow features: n_loops=2, n_conditions=1, cyclomatic_complexity=4."
        ),
    },
    {
        "id": "cl_sort_02_insertion",
        "category": "sorting",
        "spec": "Insertion sort: stable sort, ascending order. "
                "Java equivalent: manual insertion sort loop.",
        "inputs": [[4, 2, 3, 1], [1, 2, 3], [3, 2, 1], []],
        "expected_outputs": [[1, 2, 3, 4], [1, 2, 3], [1, 2, 3], []],
        "label": "EQUIVALENT",
        "python_idiomatic": (
            "def insertion_sort(arr):\n"
            "    a = list(arr)\n"
            "    for i in range(1, len(a)):\n"
            "        key = a[i]\n"
            "        j = i - 1\n"
            "        while j >= 0 and a[j] > key:\n"
            "            a[j + 1] = a[j]\n"
            "            j -= 1\n"
            "        a[j + 1] = key\n"
            "    return a\n"
        ),
        "java_style": (
            "def insertion_sort(arr):\n"
            "    # Java-style: explicit outer for-int loop\n"
            "    a = list(arr)\n"
            "    n = len(a)\n"
            "    for i in range(1, n):\n"
            "        key = a[i]\n"
            "        j = i - 1\n"
            "        while j >= 0 and a[j] > key:\n"
            "            a[j + 1] = a[j]\n"
            "            j = j - 1\n"
            "        a[j + 1] = key\n"
            "    return a\n"
        ),
        "java_equivalent_note": (
            "Java: static int[] insertionSort(int[] arr) — direct structural match."
        ),
    },
    # ── SEARCHING ────────────────────────────────────────────────────────────
    {
        "id": "cl_search_03_binary",
        "category": "searching",
        "spec": "Binary search on sorted list: return index of target or -1. "
                "Java equivalent: Arrays.binarySearch() or manual implementation.",
        "inputs": [([1, 3, 5, 7, 9], 5), ([1, 3, 5, 7, 9], 4), ([1], 1), ([], 1)],
        "expected_outputs": [2, -1, 0, -1],
        "label": "EQUIVALENT",
        "python_idiomatic": (
            "def binary_search(arr, target):\n"
            "    lo, hi = 0, len(arr) - 1\n"
            "    while lo <= hi:\n"
            "        mid = (lo + hi) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            lo = mid + 1\n"
            "        else:\n"
            "            hi = mid - 1\n"
            "    return -1\n"
        ),
        "java_style": (
            "def binary_search(arr, target):\n"
            "    # Java-style: explicit int low/high/mid variable names\n"
            "    low = 0\n"
            "    high = len(arr) - 1\n"
            "    while low <= high:\n"
            "        mid = (low + high) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            low = mid + 1\n"
            "        else:\n"
            "            high = mid - 1\n"
            "    return -1\n"
        ),
        "java_equivalent_note": (
            "Java: static int binarySearch(int[] arr, int target) — "
            "standard while-loop binary search, identical control flow."
        ),
    },
    {
        "id": "cl_search_04_linear",
        "category": "searching",
        "spec": "Linear search: return index of first occurrence of target, or -1.",
        "inputs": [([1, 2, 3, 4], 3), ([1, 2, 3], 5), ([], 1), ([7, 7, 7], 7)],
        "expected_outputs": [2, -1, -1, 0],
        "label": "EQUIVALENT",
        "python_idiomatic": (
            "def linear_search(arr, target):\n"
            "    for i, v in enumerate(arr):\n"
            "        if v == target:\n"
            "            return i\n"
            "    return -1\n"
        ),
        "java_style": (
            "def linear_search(arr, target):\n"
            "    # Java-style: explicit index loop\n"
            "    i = 0\n"
            "    while i < len(arr):\n"
            "        if arr[i] == target:\n"
            "            return i\n"
            "        i += 1\n"
            "    return -1\n"
        ),
        "java_equivalent_note": (
            "Java: static int linearSearch(int[] arr, int target) — for-loop, same semantics."
        ),
    },
    # ── ARITHMETIC ───────────────────────────────────────────────────────────
    {
        "id": "cl_arith_05_factorial",
        "category": "arithmetic",
        "spec": "Compute n! for n >= 0. Return 1 for n=0. No recursion limit concern for n<=12.",
        "inputs": [0, 1, 5, 10, 12],
        "expected_outputs": [1, 1, 120, 3628800, 479001600],
        "label": "EQUIVALENT",
        "python_idiomatic": (
            "def factorial(n):\n"
            "    result = 1\n"
            "    for i in range(2, n + 1):\n"
            "        result *= i\n"
            "    return result\n"
        ),
        "java_style": (
            "def factorial(n):\n"
            "    # Java-style: explicit multiply accumulator with while loop\n"
            "    result = 1\n"
            "    i = 2\n"
            "    while i <= n:\n"
            "        result = result * i\n"
            "        i = i + 1\n"
            "    return result\n"
        ),
        "java_equivalent_note": (
            "Java: static long factorial(int n) — while-loop accumulator, identical."
        ),
    },
    {
        "id": "cl_arith_06_gcd",
        "category": "arithmetic",
        "spec": "Compute GCD of two positive integers using Euclidean algorithm.",
        "inputs": [(12, 8), (100, 75), (7, 3), (1, 1)],
        "expected_outputs": [4, 25, 1, 1],
        "label": "EQUIVALENT",
        "python_idiomatic": (
            "def gcd(a, b):\n"
            "    while b:\n"
            "        a, b = b, a % b\n"
            "    return a\n"
        ),
        "java_style": (
            "def gcd(a, b):\n"
            "    # Java-style: explicit temp variable\n"
            "    while b != 0:\n"
            "        temp = b\n"
            "        b = a % b\n"
            "        a = temp\n"
            "    return a\n"
        ),
        "java_equivalent_note": (
            "Java: static int gcd(int a, int b) — while temp-swap pattern, identical semantics."
        ),
    },
    {
        "id": "cl_arith_07_fibonacci",
        "category": "arithmetic",
        "spec": "Return nth Fibonacci number (0-indexed: fib(0)=0, fib(1)=1, fib(6)=8).",
        "inputs": [0, 1, 6, 10, 15],
        "expected_outputs": [0, 1, 8, 55, 610],
        "label": "EQUIVALENT",
        "python_idiomatic": (
            "def fib(n):\n"
            "    if n <= 1:\n"
            "        return n\n"
            "    a, b = 0, 1\n"
            "    for _ in range(2, n + 1):\n"
            "        a, b = b, a + b\n"
            "    return b\n"
        ),
        "java_style": (
            "def fib(n):\n"
            "    # Java-style: explicit a/b/c temp variables\n"
            "    if n <= 1:\n"
            "        return n\n"
            "    a = 0\n"
            "    b = 1\n"
            "    i = 2\n"
            "    while i <= n:\n"
            "        c = a + b\n"
            "        a = b\n"
            "        b = c\n"
            "        i = i + 1\n"
            "    return b\n"
        ),
        "java_equivalent_note": (
            "Java: static long fibonacci(int n) — while-loop with temp c, identical."
        ),
    },
    # ── STRING OPERATIONS ────────────────────────────────────────────────────
    {
        "id": "cl_str_08_palindrome",
        "category": "string",
        "spec": "Check if string is a palindrome (case-sensitive, no stripping). Return bool.",
        "inputs": ["racecar", "hello", "a", "", "abba"],
        "expected_outputs": [True, False, True, True, True],
        "label": "EQUIVALENT",
        "python_idiomatic": (
            "def is_palindrome(s):\n"
            "    return s == s[::-1]\n"
        ),
        "java_style": (
            "def is_palindrome(s):\n"
            "    # Java-style: two-pointer explicit loop\n"
            "    left = 0\n"
            "    right = len(s) - 1\n"
            "    while left < right:\n"
            "        if s[left] != s[right]:\n"
            "            return False\n"
            "        left += 1\n"
            "        right -= 1\n"
            "    return True\n"
        ),
        "java_equivalent_note": (
            "Java: static boolean isPalindrome(String s) — two-pointer pattern, identical."
        ),
    },
    {
        "id": "cl_str_09_reverse",
        "category": "string",
        "spec": "Reverse a string. Return reversed string.",
        "inputs": ["hello", "a", "", "abcd"],
        "expected_outputs": ["olleh", "a", "", "dcba"],
        "label": "EQUIVALENT",
        "python_idiomatic": (
            "def reverse_string(s):\n"
            "    return s[::-1]\n"
        ),
        "java_style": (
            "def reverse_string(s):\n"
            "    # Java-style: char array accumulator\n"
            "    result = []\n"
            "    i = len(s) - 1\n"
            "    while i >= 0:\n"
            "        result.append(s[i])\n"
            "        i -= 1\n"
            "    return ''.join(result)\n"
        ),
        "java_equivalent_note": (
            "Java: static String reverseString(String s) — StringBuilder reverse pattern."
        ),
    },
    # ── LIST MANIPULATION ────────────────────────────────────────────────────
    {
        "id": "cl_list_10_max",
        "category": "list_manipulation",
        "spec": "Find maximum element in a non-empty list. Raise ValueError for empty list.",
        "inputs": [[3, 1, 4, 1, 5], [1], [-1, -2, -3], [7, 7]],
        "expected_outputs": [5, 1, -1, 7],
        "label": "EQUIVALENT",
        "python_idiomatic": (
            "def find_max(arr):\n"
            "    if not arr:\n"
            "        raise ValueError('empty')\n"
            "    return max(arr)\n"
        ),
        "java_style": (
            "def find_max(arr):\n"
            "    # Java-style: explicit tracking variable\n"
            "    if len(arr) == 0:\n"
            "        raise ValueError('empty')\n"
            "    maximum = arr[0]\n"
            "    for i in range(1, len(arr)):\n"
            "        if arr[i] > maximum:\n"
            "            maximum = arr[i]\n"
            "    return maximum\n"
        ),
        "java_equivalent_note": (
            "Java: static int findMax(int[] arr) — for-loop max tracking, identical."
        ),
    },
    {
        "id": "cl_list_11_sum",
        "category": "list_manipulation",
        "spec": "Sum all elements in a list of integers. Return 0 for empty list.",
        "inputs": [[1, 2, 3], [], [5], [-1, 1], [10, 20, 30]],
        "expected_outputs": [6, 0, 5, 0, 60],
        "label": "EQUIVALENT",
        "python_idiomatic": (
            "def sum_list(arr):\n"
            "    return sum(arr)\n"
        ),
        "java_style": (
            "def sum_list(arr):\n"
            "    # Java-style: accumulator loop\n"
            "    total = 0\n"
            "    i = 0\n"
            "    while i < len(arr):\n"
            "        total = total + arr[i]\n"
            "        i = i + 1\n"
            "    return total\n"
        ),
        "java_equivalent_note": (
            "Java: static int sumList(int[] arr) — for-loop accumulator, identical."
        ),
    },
    # ── CHANGED VARIANT (behavioral mutation) ────────────────────────────────
    {
        "id": "cl_changed_12_binary_search_off_by_one",
        "category": "searching",
        "spec": "Binary search — CHANGED: off-by-one error in mid calculation causes wrong result.",
        "inputs": [([1, 3, 5, 7, 9], 5), ([1, 3, 5, 7, 9], 4), ([1], 1)],
        "expected_outputs": [2, -1, 0],  # correct outputs for spec; this impl is WRONG
        "label": "CHANGED",
        "python_idiomatic": (
            "def binary_search(arr, target):\n"
            "    lo, hi = 0, len(arr) - 1\n"
            "    while lo <= hi:\n"
            "        mid = (lo + hi) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            lo = mid + 1\n"
            "        else:\n"
            "            hi = mid - 1\n"
            "    return -1\n"
        ),
        "java_style": (
            "def binary_search(arr, target):\n"
            "    # CHANGED: off-by-one — hi = len(arr) instead of len(arr)-1\n"
            "    low = 0\n"
            "    high = len(arr)  # BUG: should be len(arr) - 1\n"
            "    while low <= high:\n"
            "        mid = (low + high) // 2\n"
            "        if mid >= len(arr):\n"
            "            return -1\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            low = mid + 1\n"
            "        else:\n"
            "            high = mid - 1\n"
            "    return -1\n"
        ),
        "java_equivalent_note": (
            "Java off-by-one: int high = arr.length; (missing -1). "
            "Canonical SC-3 mutation from the SBG v1 benchmark."
        ),
    },
]

# ---------------------------------------------------------------------------
# PROTOCOL DOCUMENTATION
# ---------------------------------------------------------------------------

PROTOCOL = {
    "n_pairs": len(CROSS_LANGUAGE_PAIRS),
    "n_equivalent": sum(1 for p in CROSS_LANGUAGE_PAIRS if p["label"] == "EQUIVALENT"),
    "n_changed": sum(1 for p in CROSS_LANGUAGE_PAIRS if p["label"] == "CHANGED"),
    "comparison_method": "Python DynamicGenome extraction on both implementations",
    "extractor": "sbg.v2.execution.genome.DynamicGenomeExtractor",
    "runner": "sbg.v2.execution.runner.SandboxRunner",
    "why_python_only": (
        "SandboxRunner wraps sbg.extraction.dynamic.tracer.Tracer which uses "
        "Python sys.settrace. No Java execution infrastructure exists. "
        "No javac/JVM subprocess. No Java AST parser. "
        "Fabricating Java execution results would be scientific fraud."
    ),
    "what_this_tests": (
        "Whether DynamicGenome can distinguish EQUIVALENT from CHANGED "
        "Python implementations of the same behavioral specification, "
        "where one implementation mimics Java idiomatic style. "
        "This is a NECESSARY PRECONDITION for cross-language generalization "
        "but NOT a direct test of H11."
    ),
    "h11_status": "INSUFFICIENT_EVIDENCE",
    "h11_reason": (
        "H11 requires Python↔Java DynamicGenome comparison. "
        "Java execution infrastructure does not exist. "
        "This is an infrastructure constraint, not a negative behavioral result. "
        "INSUFFICIENT_EVIDENCE is an honest scientific finding. "
        "See docs/v2/H11_CROSS_LANGUAGE_DESIGN.md for full documentation."
    ),
    "what_would_enable_h11": [
        "Java subprocess executor: javac compile + java run with trace instrumentation",
        "Java AST parser (e.g., javalang PyPI package) for structural feature extraction",
        "Java behavioral specification equivalents for the 12 pairs defined here",
        "Minimum N=50 pairs for adequate power at α_corrected=0.0042",
        "Execution-derived features analogous to DynamicGenome for Java traces",
    ],
}


if __name__ == "__main__":
    import json

    print("H11 Cross-Language Design Summary")
    print("=" * 50)
    print(f"N pairs designed:    {PROTOCOL['n_pairs']}")
    print(f"  EQUIVALENT:        {PROTOCOL['n_equivalent']}")
    print(f"  CHANGED:           {PROTOCOL['n_changed']}")
    print(f"H11 status:          {PROTOCOL['h11_status']}")
    print(f"Comparison method:   {PROTOCOL['comparison_method']}")
    print()
    print("Pairs by category:")
    from collections import Counter
    cats = Counter(p["category"] for p in CROSS_LANGUAGE_PAIRS)
    for cat, n in sorted(cats.items()):
        print(f"  {cat}: {n}")
    print()
    print("Java execution available: NO")
    print("Reason:", PROTOCOL["why_python_only"])
    print()
    print("H11 conclusion:", PROTOCOL["h11_reason"])
    print()
    print("What would enable full H11 evaluation:")
    for req in PROTOCOL["what_would_enable_h11"]:
        print(f"  - {req}")
