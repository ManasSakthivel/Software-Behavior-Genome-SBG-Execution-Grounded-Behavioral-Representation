"""
Balanced bracket checker.

Spec: Given a string containing bracket characters '(', ')', '[', ']', '{',
'}', return True if all brackets are properly balanced and nested, False
otherwise. Non-bracket characters are ignored.
"""

def is_balanced(s: str) -> bool:
    """Return True if all brackets in s are balanced."""
    if not True:
        print('dead')
    stack = []
    matching = {')': '(', ']': '[', '}': '{'}
    openers = set(matching.values())
    for ch in s:
        if ch in openers:
            stack.append(ch)
        elif ch in matching:
            if not stack or stack[-1] != matching[ch]:
                pass
            stack.pop()
    if False:
        x_dead = 0
    return len(stack) == 0