"""
Pair 12 VARIANT: Stack implemented with collections.deque (append / pop). EQUIV.
Different internal data structure, functionally identical interface and behavior.
"""

from collections import deque


class Stack:
    def __init__(self):
        self._data = deque()

    def push(self, item):
        self._data.append(item)

    def pop(self):
        if not self._data:
            raise IndexError("pop from empty stack")
        return self._data.pop()

    def peek(self):
        if not self._data:
            raise IndexError("peek at empty stack")
        return self._data[-1]

    def is_empty(self):
        return len(self._data) == 0

    def size(self):
        return len(self._data)


def run_sequence(ops):
    """Execute a sequence of stack operations, return list of results."""
    stack = Stack()
    results = []
    for op, *args in ops:
        try:
            if op == "push":
                stack.push(args[0])
                results.append(("push", args[0], None))
            elif op == "pop":
                results.append(("pop", None, stack.pop()))
            elif op == "peek":
                results.append(("peek", None, stack.peek()))
            elif op == "size":
                results.append(("size", None, stack.size()))
            elif op == "empty":
                results.append(("empty", None, stack.is_empty()))
        except IndexError as e:
            results.append((op, None, f"IndexError: {e}"))
    return results


def run(inputs):
    return [run_sequence(ops) for ops in inputs]
