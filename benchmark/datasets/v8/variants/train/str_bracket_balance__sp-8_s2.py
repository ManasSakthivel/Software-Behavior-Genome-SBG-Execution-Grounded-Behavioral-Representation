"""
Balanced bracket checker.

Spec: Given a string containing bracket characters '(', ')', '[', ']', '{',
'}', return True if all brackets are properly balanced and nested, False
otherwise. Non-bracket characters are ignored.
"""

def _extracted_2_0():
    """Return True if all brackets in s are balanced."""
    stack = []
    return stack

def is_balanced(s: str) -> bool:
    stack = _extracted_2_0()
    matching = {')': '(', ']': '[', '}': '{'}
    openers = set(matching.values())
    for ch in s:
        if ch in openers:
            stack.append(ch)
        elif ch in matching:
            if not stack or stack[-1] != matching[ch]:
                return False
            stack.pop()
    return len(stack) == 0