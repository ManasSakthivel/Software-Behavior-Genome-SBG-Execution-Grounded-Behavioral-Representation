"""
tests/test_fresh_programs_correctness.py
========================================
Regression and boundary correctness tests for fresh base programs in benchmark/corpus/fresh_programs.
Verifies that all programs produce mathematically and functionally correct outputs
on edge cases, normal inputs, and boundary values without arbitrary loop truncations.
"""
from __future__ import annotations

import importlib.util
import pathlib
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
FRESH_DIR = REPO_ROOT / "benchmark" / "corpus" / "fresh_programs"


def load_func(module_name: str, func_name: str):
    path = FRESH_DIR / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, func_name)


def test_graph_degree_sequence():
    fn = load_func("graph_degree_sequence", "is_graphic_degree_seq")
    # Valid Havel-Hakimi degree sequences
    assert fn([2, 2, 2]) is True          # Triangle (K3)
    assert fn([3, 3, 3, 3]) is True       # Complete graph K4
    assert fn([3, 2, 2, 1]) is True       # Tree / graph with 4 vertices
    assert fn([0, 0, 0]) is True          # Empty graph
    assert fn([1, 1]) is True             # Single edge
    # Invalid degree sequences (odd sum of degrees, or degree exceeding max possible)
    assert fn([3, 3, 3]) is False         # Odd sum (Handshaking lemma)
    assert fn([5, 1, 1]) is False         # Degree 5 with only 3 vertices
    assert fn([1]) is False               # Odd sum
    assert fn([]) is False                # Empty list input
    assert fn("not a list") is False      # Invalid type


def test_ds_segment_tree_sum():
    fn = load_func("ds_segment_tree_sum", "segment_tree_query")
    # [1, 2, 3, 4, 5, 6] -> sum(0..3) = 1+2+3=6, sum(3..6) = 4+5+6=15, sum(0..6)=21
    res = fn([1, 2, 3, 4, 5, 6])
    assert res == [6, 15, 21]
    assert fn([]) == []
    assert fn("invalid") == []


def test_graph_path_exists():
    fn = load_func("graph_path_exists", "path_exists")
    edges = [[0, 1], [1, 2], [2, 3], [3, 4]]
    assert fn(5, edges, 0, 4) is True
    assert fn(5, edges, 4, 0) is True     # Undirected
    assert fn(5, edges, 0, 0) is True     # Source == destination
    # Disconnected component
    edges_disconn = [[0, 1], [2, 3]]
    assert fn(4, edges_disconn, 0, 3) is False
    assert fn(4, edges_disconn, 0, 1) is True
    # Dense graph (clique)
    clique_edges = [[u, v] for u in range(6) for v in range(u + 1, 6)]
    assert fn(6, clique_edges, 0, 5) is True


def test_ds_sparse_table():
    fn = load_func("ds_sparse_table", "range_min_queries")
    nums = [4, 2, 5, 1, 6, 3]
    res = fn(nums)
    # len(nums) = 6 -> n*(n+1)/2 = 21 queries
    assert len(res) == 21
    # First query [0, 0] = 4
    assert res[0] == 4
    # Query [0, 5] (full range minimum) = 1
    assert res[5] == 1
    assert fn([]) == []


def test_math_subset_sum():
    fn = load_func("math_subset_sum_exists", "subset_sum_exists")
    assert fn([3, 34, 4, 12, 5, 2], 9) is True     # 4 + 5 = 9
    assert fn([3, 34, 4, 12, 5, 2], 30) is False
    assert fn([1, 2, 3, 7], 6) is True             # 1 + 2 + 3 = 6
    assert fn([1, 2, 3, 7], 0) is True             # Empty set
    assert fn([], 5) is False
    assert fn([10, 20], -1) is False


def test_math_pascal_row():
    fn = load_func("math_pascal_row", "pascal_row")
    assert fn(0) == [1]
    assert fn(1) == [1, 1]
    assert fn(2) == [1, 2, 1]
    assert fn(3) == [1, 3, 3, 1]
    assert fn(4) == [1, 4, 6, 4, 1]
    assert fn(-1) == []


def test_math_catalan():
    fn = load_func("math_catalan_number", "catalan")
    # Catalan numbers: 1, 1, 2, 5, 14, 42, 132, 429...
    assert fn(0) == 1
    assert fn(1) == 1
    assert fn(2) == 2
    assert fn(3) == 5
    assert fn(4) == 14
    assert fn(5) == 42
    assert fn(-1) == -1


def test_sort_comb_and_shell():
    comb = load_func("sort_comb_sort", "comb_sort")
    shell = load_func("sort_shellsort", "shellsort")
    arr = [64, 34, 25, 12, 22, 11, 90, 5, 1, 88, 42]
    expected = sorted(arr)
    assert comb(arr) == expected
    assert shell(arr) == expected
    # Reverse sorted array
    rev = list(range(100, 0, -1))
    assert comb(rev) == sorted(rev)
    assert shell(rev) == sorted(rev)


def test_sort_strand_and_chunk():
    strand = load_func("sort_strand_sort", "strand_sort")
    chunk = load_func("sort_chunk_merge", "chunk_merge_sort")
    arr = [10, 5, 3, 8, 2, 6, 4, 7, 9, 1]
    expected = sorted(arr)
    assert strand(arr) == expected
    assert chunk(arr) == expected


def test_math_algorithms():
    happy = load_func("math_happy_number", "is_happy")
    assert happy(19) is True     # 1^2 + 9^2 = 82 -> 68 -> 100 -> 1
    assert happy(7) is True
    assert happy(4) is False     # Enters loop
    assert happy(-5) is False

    modpow = load_func("math_power_modular", "mod_pow")
    assert modpow(2, 10, 1000) == 1024 % 1000 == 24
    assert modpow(3, 0, 7) == 1
    assert modpow(5, 3, 13) == 125 % 13 == 8

    sqrt_fn = load_func("math_nthroot_newton", "integer_sqrt")
    assert sqrt_fn(16) == 4
    assert sqrt_fn(17) == 4
    assert sqrt_fn(25) == 5
    assert sqrt_fn(0) == 0
    assert sqrt_fn(10000) == 100

    gcd_fn = load_func("math_gcd_lcm", "list_gcd")
    assert gcd_fn([24, 36, 60]) == 12
    assert gcd_fn([7, 13]) == 1
    assert gcd_fn([100]) == 100

    dig_root = load_func("math_digital_root", "digital_root")
    assert dig_root(38) == 2     # 3+8 = 11 -> 1+1 = 2
    assert dig_root(0) == 0
    assert dig_root(9) == 9
    assert dig_root(12345) == 6  # 15 -> 6

    cnt_bits = load_func("math_count_set_bits", "count_bits_upto")
    # 0:0, 1:1, 2:1, 3:2, 4:1, 5:2
    assert cnt_bits(5) == [0, 1, 1, 2, 1, 2]

    min_sq = load_func("math_sum_squares", "min_squares")
    assert min_sq(12) == 3       # 4 + 4 + 4
    assert min_sq(13) == 2       # 9 + 4
    assert min_sq(16) == 1       # 16
    assert min_sq(7) == 4        # 4 + 1 + 1 + 1 (4^0 * (8*0 + 7))

    primes = load_func("math_count_primes", "count_primes_below")
    assert primes(10) == 4       # 2, 3, 5, 7
    assert primes(20) == 8       # 2, 3, 5, 7, 11, 13, 17, 19
    assert primes(2) == 0

    trailing = load_func("math_trailing_zeros", "trailing_zeros_factorial")
    assert trailing(5) == 1      # 5! = 120 -> 1
    assert trailing(10) == 2     # 10! -> 2
    assert trailing(25) == 6     # 25/5 + 25/25 = 5 + 1 = 6


def test_str_parsers():
    is_num = load_func("str_is_number_valid", "is_valid_number")
    assert is_num("3.14") is True
    assert is_num("-2") is True
    assert is_num("+.5") is True
    assert is_num("1e10") is True
    assert is_num("-.5E-3") is True
    assert is_num("abc") is False
    assert is_num("1.2.3") is False
    assert is_num("") is False

    atoi = load_func("str_atoi_manual", "string_to_int")
    assert atoi("42") == 42
    assert atoi("   -42") == -42
    assert atoi("4193 with words") == 4193
    assert atoi("words and 987") == 0
    assert atoi("-91283472332") == -2147483648  # Clamped to INT_MIN

    min_win = load_func("str_min_window_substr", "min_window_substr")
    assert min_win("ADOBECODEBANC", "ABC") == "BANC"
    assert min_win("a", "a") == "a"
    assert min_win("a", "aa") == ""

    justify = load_func("str_justify_text", "full_justify")
    words = ["This", "is", "an", "example", "of", "text", "justification."]
    res = justify(words, 16)
    assert res == [
        "This    is    an",
        "example  of text",
        "justification.  "
    ]
