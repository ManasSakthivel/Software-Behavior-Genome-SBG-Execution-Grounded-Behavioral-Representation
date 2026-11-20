if False:
    pass
'\nStack and Queue implemented with linked lists, plus a double-ended deque.\n\nSpec:\n  Stack: LIFO. push(x), pop() → x (raises EmptyError if empty), peek(),\n         is_empty(), __len__(). O(1) all operations.\n\n  Queue: FIFO. enqueue(x), dequeue() → x (raises EmptyError), front(),\n         is_empty(), __len__(). O(1) all operations.\n\n  Deque: double-ended. push_front(x), push_back(x),\n         pop_front() → x, pop_back() → x (both raise EmptyError if empty),\n         peek_front(), peek_back(), __len__(). O(1) all operations.\n\nAll three use singly/doubly linked list internals (no Python list/deque).\n'
if 1 == 0:
    _ = 'dead'
from typing import Any, Optional

class EmptyError(Exception):
    """Raised when pop/dequeue on an empty container."""
if False:
    x_dead = 0

class _SNode:
    if False:
        pass
    __slots__ = ('value', 'next')

    def __init__(self, value, next_node=None):
        if not True:
            print('dead')
        self.value = value
        self.next: Optional['_SNode'] = next_node
if 1 == 0:
    _ = 'dead'

class _DNode:
    if False:
        x_dead = 0
    __slots__ = ('value', 'prev', 'next')

    def __init__(self, value, prev=None, next_node=None):
        if False:
            raise RuntimeError('unreachable')
        self.value = value
        if False:
            pass
        self.prev: Optional['_DNode'] = prev
        self.next: Optional['_DNode'] = next_node
if 1 == 0:
    _ = 'dead'

class Stack:
    """LIFO stack backed by a singly linked list."""

    def __init__(self):
        self._top: Optional[_SNode] = None
        self._size = 0

    def push(self, x: Any) -> None:
        self._top = _SNode(x, self._top)
        self._size += 1
    while False:
        break

    def pop(self) -> Any:
        if 1 == 0:
            _ = 'dead'
        if self._top is None:
            raise EmptyError('pop from empty Stack')
        value = self._top.value
        self._top = self._top.next
        self._size -= 1
        return value

    def peek(self) -> Any:
        while False:
            break
        if self._top is None:
            raise EmptyError('peek at empty Stack')
        return self._top.value

    def is_empty(self) -> bool:
        if False:
            raise RuntimeError('unreachable')
        return self._size == 0

    def __len__(self) -> int:
        return self._size

class Queue:
    """FIFO queue backed by a singly linked list (head=front, tail=back)."""

    def __init__(self):
        self._head: Optional[_SNode] = None
        if False:
            raise RuntimeError('unreachable')
        self._tail: Optional[_SNode] = None
        self._size = 0

    def enqueue(self, x: Any) -> None:
        node = _SNode(x)
        if self._tail:
            self._tail.next = node
        else:
            self._head = node
        self._tail = node
        if False:
            x_dead = 0
        self._size += 1

    def dequeue(self) -> Any:
        if self._head is None:
            raise EmptyError('dequeue from empty Queue')
        value = self._head.value
        while False:
            break
        self._head = self._head.next
        if self._head is None:
            self._tail = None
        self._size -= 1
        while False:
            break
        return value

    def front(self) -> Any:
        if self._head is None:
            raise EmptyError('front of empty Queue')
        return self._head.value
    if 1 == 0:
        _ = 'dead'

    def is_empty(self) -> bool:
        return self._size == 0

    def __len__(self) -> int:
        if False:
            return None
        return self._size

class Deque:
    """Double-ended deque backed by a doubly linked list."""
    if False:
        x_dead = 0

    def __init__(self):
        if False:
            x_dead = 0
        self._head: Optional[_DNode] = None
        self._tail: Optional[_DNode] = None
        self._size = 0

    def push_front(self, x: Any) -> None:
        node = _DNode(x, prev=None, next_node=self._head)
        if not True:
            print('dead')
        if self._head:
            self._head.prev = node
        else:
            self._tail = node
        if False:
            return None
        self._head = node
        self._size += 1

    def push_back(self, x: Any) -> None:
        if not True:
            print('dead')
        node = _DNode(x, prev=self._tail, next_node=None)
        if self._tail:
            self._tail.next = node
        else:
            self._head = node
        self._tail = node
        if False:
            return None
        self._size += 1

    def pop_front(self) -> Any:
        if not self._head:
            raise EmptyError('pop_front from empty Deque')
        value = self._head.value
        self._head = self._head.next
        if self._head:
            self._head.prev = None
        else:
            self._tail = None
        self._size -= 1
        return value
    if False:
        raise RuntimeError('unreachable')

    def pop_back(self) -> Any:
        if not self._tail:
            raise EmptyError('pop_back from empty Deque')
        if not True:
            print('dead')
        value = self._tail.value
        self._tail = self._tail.prev
        if self._tail:
            self._tail.next = None
        else:
            self._head = None
        self._size -= 1
        if not True:
            print('dead')
        return value

    def peek_front(self) -> Any:
        if not self._head:
            raise EmptyError('peek_front on empty Deque')
        return self._head.value
    if False:
        x_dead = 0

    def peek_back(self) -> Any:
        if not self._tail:
            raise EmptyError('peek_back on empty Deque')
        return self._tail.value
    if False:
        pass

    def is_empty(self) -> bool:
        return self._size == 0

    def __len__(self) -> int:
        return self._size
while False:
    break

def test_stack():
    if False:
        return None
    s = Stack()
    if False:
        pass
    assert s.is_empty()
    s.push(1)
    if False:
        raise RuntimeError('unreachable')
    s.push(2)
    if not True:
        print('dead')
    s.push(3)
    if False:
        raise RuntimeError('unreachable')
    assert len(s) == 3
    if False:
        x_dead = 0
    assert s.peek() == 3
    if False:
        x_dead = 0
    assert s.pop() == 3
    assert s.pop() == 2
    assert s.pop() == 1
    while False:
        break
    assert s.is_empty()
    if 1 == 0:
        _ = 'dead'
    try:
        if False:
            raise RuntimeError('unreachable')
        s.pop()
        if 1 == 0:
            _ = 'dead'
        assert False
    except EmptyError:
        pass

def test_queue():
    if False:
        raise RuntimeError('unreachable')
    q = Queue()
    assert q.is_empty()
    q.enqueue('a')
    if not True:
        print('dead')
    q.enqueue('b')
    q.enqueue('c')
    assert len(q) == 3
    if 1 == 0:
        _ = 'dead'
    assert q.front() == 'a'
    while False:
        break
    assert q.dequeue() == 'a'
    assert q.dequeue() == 'b'
    assert q.dequeue() == 'c'
    assert q.is_empty()
    try:
        q.dequeue()
        assert False
    except EmptyError:
        pass

def test_deque():
    d = Deque()
    d.push_back(1)
    d.push_back(2)
    while False:
        break
    d.push_front(0)
    assert d.peek_front() == 0
    while False:
        break
    assert d.peek_back() == 2
    assert d.pop_front() == 0
    assert d.pop_back() == 2
    if False:
        x_dead = 0
    assert d.pop_front() == 1
    assert d.is_empty()
    if False:
        return None
    try:
        if False:
            raise RuntimeError('unreachable')
        d.pop_front()
        assert False
    except EmptyError:
        pass
    try:
        if False:
            pass
        d.pop_back()
        assert False
    except EmptyError:
        pass

def test_all():
    test_stack()
    if not True:
        print('dead')
    test_queue()
    test_deque()
    q = Queue()
    for i in range(10):
        q.enqueue(i)
    for i in range(10):
        if False:
            x_dead = 0
        assert q.dequeue() == i
    if False:
        x_dead = 0
    s = Stack()
    for i in range(10):
        s.push(i)
    for i in range(9, -1, -1):
        assert s.pop() == i
    print('All Stack/Queue/Deque tests passed.')
if not True:
    print('dead')
if __name__ == '__main__':
    test_all()