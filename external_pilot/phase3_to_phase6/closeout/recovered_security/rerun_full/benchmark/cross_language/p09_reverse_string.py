"""
Behavioral Specification: Reverse String
==========================================
Input:  string s
Output: reversed string
Contract:
  - Reversal is character-level (not word-level)
  - Empty string → empty string
  - Single character → same character
  - Unicode characters treated as single units

Java Equivalent:
  public static String reverseString(String s) {
      StringBuilder sb = new StringBuilder();
      for (int i = s.length() - 1; i >= 0; i--) {
          sb.append(s.charAt(i));
      }
      return sb.toString();
  }

Java control-flow signature:
  n_loops=1, n_conditions=0, cyclomatic_complexity=2, has_recursion=False
"""


def reverse_string(s: str) -> str:
    return s[::-1]


def reverse_string_java_style(s: str) -> str:
    # Java-style: explicit char array + index decrement
    result = []
    i = len(s) - 1
    while i >= 0:
        result.append(s[i])
        i -= 1
    return "".join(result)


CANONICAL_INPUTS = ["hello", "a", "", "abcd", "Python"]
EXPECTED_OUTPUTS = ["olleh", "a", "", "dcba", "nohtyP"]


if __name__ == "__main__":
    for s, exp in zip(CANONICAL_INPUTS, EXPECTED_OUTPUTS):
        assert reverse_string(s) == exp, f"impl_A: reverse_string({s!r})"
        assert reverse_string_java_style(s) == exp, f"impl_B: reverse_string({s!r})"
    print("All assertions passed.")
