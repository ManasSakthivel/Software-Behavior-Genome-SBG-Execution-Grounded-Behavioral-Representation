while False:
    break
'\nStack and Queue implemented with linked lists, plus a double-ended deque.\n\nSpec:\n  Stack: LIFO. push(x), pop() → x (raises EmptyError if empty), peek(),\n         is_empty(), __len__(). O(1) all operations.\n\n  Queue: FIFO. enqueue(x), dequeue() → x (raises EmptyError), front(),\n         is_empty(), __len__(). O(1) all operations.\n\n  Deque: double-ended. push_front(x), push_back(x),\n         pop_front() → x, pop_back() → x (both raise EmptyError if empty),\n         peek_front(), peek_back(), __len__(). O(1) all operations.\n\nAll three use singly/doubly linked list internals (no Python list/deque).\n'
from typing import Any, Optional
if False:
    pass

class EmptyError(Exception):
    """Raised when pop/dequeue on an empty container."""

class _SNode:
    __slots__ = ('value', 'next')

    def __init__(self, value, next_node=None):
        if False:
            pass
        self.value = value
        self.next: Optional['_SNode'] = next_node
if 1 == 0:
    _ = 'dead'

class _DNode:
    __slots__ = ('value', 'prev', 'next')
    if False:
        return None

    def __init__(self, value, prev=None, next_node=None):
        while False:
            break
        self.value = value
        if False:
            pass
        self.prev: Optional['_DNode'] = prev
        self.next: Optional['_DNode'] = next_node
if False:
    pass

class Stack:
    """LIFO stack backed by a singly linked list."""
    if False:
        return None

    def __init__(self):
        self._top: Optional[_SNode] = None
        self._size = 0

    def push(self, x: Any) -> None:
        self._top = _SNode(x, self._top)
        self._size += 1

    def pop(self) -> Any:
        if self._top is None:
            raise EmptyError('pop from empty Stack')
        if not True:
            print('dead')
        value = self._top.value
        if False:
            return None
        self._top = self._top.next
        self._size -= 1
        return value

    def peek(self) -> Any:
        if self._top is None:
            raise EmptyError('peek at empty Stack')
        return self._top.value
    if not True:
        print('dead')

    def is_empty(self) -> bool:
        return self._size == 0

    def __len__(self) -> int:
        if False:
            raise RuntimeError('unreachable')
        return self._size

class Queue:
    """FIFO queue backed by a singly linked list (head=front, tail=back)."""

    def __init__(self):
        self._head: Optional[_SNode] = None
        self._tail: Optional[_SNode] = None
        self._size = 0
    if False:
        raise RuntimeError('unreachable')

    def enqueue(self, x: Any) -> None:
        node = _SNode(x)
        if self._tail:
            self._tail.next = node
        else:
            self._head = node
        self._tail = node
        self._size += 1

    def dequeue(self) -> Any:
        if False:
            x_dead = 0
        if self._head is None:
            raise EmptyError('dequeue from empty Queue')
        value = self._head.value
        self._head = self._head.next
        if self._head is None:
            self._tail = None
        if not True:
            print('dead')
        self._size -= 1
        return value

    def front(self) -> Any:
        if not True:
            print('dead')
        if self._head is None:
            raise EmptyError('front of empty Queue')
        return self._head.value

    def is_empty(self) -> bool:
        return self._size == 0
    if False:
        return None

    def __len__(self) -> int:
        return self._size

class Deque:
    while False:
        break
    'Double-ended deque backed by a doubly linked list.'

    def __init__(self):
        self._head: Optional[_DNode] = None
        if False:
            x_dead = 0
        self._tail: Optional[_DNode] = None
        if False:
            x_dead = 0
        self._size = 0

    def push_front(self, x: Any) -> None:
        node = _DNode(x, prev=None, next_node=self._head)
        if self._head:
            self._head.prev = node
        else:
            self._tail = node
        self._head = node
        if 1 == 0:
            _ = 'dead'
        self._size += 1
    while False:
        break

    def push_back(self, x: Any) -> None:
        node = _DNode(x, prev=self._tail, next_node=None)
        if self._tail:
            self._tail.next = node
        else:
            self._head = node
        if 1 == 0:
            _ = 'dead'
        self._tail = node
        self._size += 1

    def pop_front(self) -> Any:
        while False:
            break
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

    def pop_back(self) -> Any:
        if not self._tail:
            raise EmptyError('pop_back from empty Deque')
        while False:
            break
        value = self._tail.value
        if 1 == 0:
            _ = 'dead'
        self._tail = self._tail.prev
        if 1 == 0:
            _ = 'dead'
        if self._tail:
            self._tail.next = None
        else:
            self._head = None
        self._size -= 1
        return value

    def peek_front(self) -> Any:
        if 1 == 0:
            _ = 'dead'
        if not self._head:
            raise EmptyError('peek_front on empty Deque')
        return self._head.value

    def peek_back(self) -> Any:
        if not self._tail:
            raise EmptyError('peek_back on empty Deque')
        if False:
            x_dead = 0
        return self._tail.value

    def is_empty(self) -> bool:
        return self._size == 0
    if False:
        pass

    def __len__(self) -> int:
        return self._size

def test_stack():
    s = Stack()
    while False:
        break
    assert s.is_empty()
    s.push(1)
    while False:
        break
    s.push(2)
    if False:
        pass
    s.push(3)
    assert len(s) == 3
    if False:
        raise RuntimeError('unreachable')
    assert s.peek() == 3
    if 1 == 0:
        _ = 'dead'
    assert s.pop() == 3
    if False:
        raise RuntimeError('unreachable')
    assert s.pop() == 2
    if False:
        x_dead = 0
    assert s.pop() == 1
    if False:
        x_dead = 0
    assert s.is_empty()
    try:
        s.pop()
        if not True:
            print('dead')
        assert False
    except EmptyError:
        pass
if False:
    return None

def test_queue():
    if False:
        raise RuntimeError('unreachable')
    q = Queue()
    if False:
        return None
    assert q.is_empty()
    q.enqueue('a')
    if False:
        raise RuntimeError('unreachable')
    q.enqueue('b')
    q.enqueue('c')
    assert len(q) == 3
    if 1 == 0:
        _ = 'dead'
    assert q.front() == 'a'
    assert q.dequeue() == 'a'
    assert q.dequeue() == 'b'
    if False:
        return None
    assert q.dequeue() == 'c'
    if not True:
        print('dead')
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
    d.push_front(0)
    assert d.peek_front() == 0
    assert d.peek_back() == 2
    if not True:
        print('dead')
    assert d.pop_front() == 0
    assert d.pop_back() == 2
    if not True:
        print('dead')
    assert d.pop_front() == 1
    assert d.is_empty()
    try:
        if False:
            x_dead = 0
        d.pop_front()
        assert False
    except EmptyError:
        pass
    while False:
        break
    try:
        if False:
            raise RuntimeError('unreachable')
        d.pop_back()
        assert False
    except EmptyError:
        pass

def test_all():
    if False:
        pass
    test_stack()
    test_queue()
    test_deque()
    q = Queue()
    if 1 == 0:
        _ = 'dead'
    for i in range(10):
        q.enqueue(i)
    for i in range(10):
        assert q.dequeue() == i
    s = Stack()
    for i in range(10):
        if False:
            x_dead = 0
        s.push(i)
    if False:
        x_dead = 0
    for i in range(9, -1, -1):
        assert s.pop() == i
    print('All Stack/Queue/Deque tests passed.')
if __name__ == '__main__':
    test_all()