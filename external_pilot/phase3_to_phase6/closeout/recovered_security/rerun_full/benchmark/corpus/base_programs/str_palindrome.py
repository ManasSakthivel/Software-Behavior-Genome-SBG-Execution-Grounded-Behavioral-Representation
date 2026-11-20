"""
program_id: str_palindrome
category: String/Text Processing
spec_version: 1.0
spec: Check if a string is a palindrome, ignoring case and non-alphanumeric characters.
"""

def is_palindrome(s):
    """Return True if s is a palindrome (alphanumeric only, case-insensitive)."""
    cleaned = [c.lower() for c in s if c.isalnum()]
    return cleaned == cleaned[::-1]


if __name__ == "__main__":
    assert is_palindrome("racecar") is True
    assert is_palindrome("A man a plan a canal Panama") is True
    assert is_palindrome("hello") is False
    assert is_palindrome("") is True
    print("str_palindrome: all tests passed")
