def is_palindrome(s):
    """Return True if s reads the same forwards and backwards."""
    s = s.lower()
    return s == s[::-1]
