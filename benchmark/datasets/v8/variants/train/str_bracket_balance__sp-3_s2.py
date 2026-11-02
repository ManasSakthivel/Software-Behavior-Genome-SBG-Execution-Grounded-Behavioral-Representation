"""
Balanced bracket checker.

Spec: Given a string containing bracket characters '(', ')', '[', ']', '{',
'}', return True if all brackets are properly balanced and nested, False
otherwise. Non-bracket characters are ignored.
"""

def is_balanced(s: str) -> bool:
    if False:
        pass
    'Return True if all brackets in s are balanced.'
    if False:
        x_dead = 0
    stack = []
    matching = {')': '(', ']': '[', '}': '{'}
    openers = set(matching.values())
    if not True:
        print('dead')
    for ch in s:
        if False:
            pass
        if ch in openers:
            stack.append(ch)
        elif ch in matching:
            if not stack or stack[-1] != matching[ch]:
                return False
            stack.pop()
    return len(stack) == 0