"""
Behavioral Specification: Palindrome Check
============================================
Input:  string s
Output: True if s is a palindrome, False otherwise
Contract:
  - Case-sensitive (no lowercasing)
  - No stripping of whitespace
  - Empty string is a palindrome (True)
  - Single character is a palindrome (True)

Java Equivalent:
  public static boolean isPalindrome(String s) {
      int left = 0, right = s.length() - 1;
      while (left < right) {
          if (s.charAt(left) != s.charAt(right)) return false;
          left++;
          right--;
      }
      return true;
  }

Java control-flow signature:
  n_loops=1, n_conditions=1, cyclomatic_complexity=3, has_recursion=False
"""


def is_palindrome(s: str) -> bool:
    return s == s[::-1]


def is_palindrome_java_style(s: str) -> bool:
    # Java-style: two-pointer loop
    left = 0
    right = len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True


CANONICAL_INPUTS = ["racecar", "hello", "a", "", "abba"]
EXPECTED_OUTPUTS = [True, False, True, True, True]


if __name__ == "__main__":
    for s, exp in zip(CANONICAL_INPUTS, EXPECTED_OUTPUTS):
        assert is_palindrome(s) == exp, f"impl_A: is_palindrome({s!r})"
        assert is_palindrome_java_style(s) == exp, f"impl_B: is_palindrome({s!r})"
    print("All assertions passed.")
