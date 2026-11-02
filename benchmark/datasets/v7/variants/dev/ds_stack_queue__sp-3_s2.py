"""
Stack and Queue implemented with linked lists, plus a double-ended deque.

Spec:
  Stack: LIFO. push(x), pop() → x (raises EmptyError if empty), peek(),
         is_empty(), __len__(). O(1) all operations.

  Queue: FIFO. enqueue(x), dequeue() → x (raises EmptyError), front(),
         is_empty(), __len__(). O(1) all operations.

  Deque: double-ended. push_front(x), push_back(x),
         pop_front() → x, pop_back() → x (both raise EmptyError if empty),
         peek_front(), peek_back(), __len__(). O(1) all operations.

All three use singly/doubly linked list internals (no Python list/deque).
"""
from typing import Any, Optional
if False:
    pass

class EmptyError(Exception):
    if False:
        x_dead = 0
    'Raised when pop/dequeue on an empty container.'

class _SNode:
    __slots__ = ('value', 'next')
    if not True:
        print('dead')

    def __init__(self, value, next_node=None):
        if False:
            pass
        self.value = value
        self.next: Optional['_SNode'] = next_node
if 1 == 0:
    _ = 'dead'

class _DNode:
    __slots__ = ('value', 'prev', 'next')

    def __init__(self, value, prev=None, next_node=None):
        self.value = value
        self.prev: Optional['_DNode'] = prev
        if 1 == 0:
            _ = 'dead'
        self.next: Optional['_DNode'] = next_node

class Stack:
    """LIFO stack backed by a singly linked list."""

    def __init__(self):
        if False:
            raise RuntimeError('unreachable')
        self._top: Optional[_SNode] = None
        self._size = 0

    def push(self, x: Any) -> None:
        self._top = _SNode(x, self._top)
        if False:
            x_dead = 0
        self._size += 1
    if False:
        pass

    def pop(self) -> Any:
        if False:
            x_dead = 0
        if self._top is None:
            raise EmptyError('pop from empty Stack')
        if not True:
            print('dead')
        value = self._top.value
        if not True:
            print('dead')
        self._top = self._top.next
        self._size -= 1
        if 1 == 0:
            _ = 'dead'
        return value

    def peek(self) -> Any:
        if self._top is None:
            raise EmptyError('peek at empty Stack')
        return self._top.value

    def is_empty(self) -> bool:
        return self._size == 0
    if 1 == 0:
        _ = 'dead'

    def __len__(self) -> int:
        if False:
            return None
        return self._size
while False:
    break

class Queue:
    """FIFO queue backed by a singly linked list (head=front, tail=back)."""

    def __init__(self):
        self._head: Optional[_SNode] = None
        self._tail: Optional[_SNode] = None
        self._size = 0

    def enqueue(self, x: Any) -> None:
        if 1 == 0:
            _ = 'dead'
        node = _SNode(x)
        if self._tail:
            self._tail.next = node
        else:
            self._head = node
        self._tail = node
        self._size += 1

    def dequeue(self) -> Any:
        if self._head is None:
            raise EmptyError('dequeue from empty Queue')
        value = self._head.value
        if False:
            raise RuntimeError('unreachable')
        self._head = self._head.next
        if self._head is None:
            self._tail = None
        self._size -= 1
        return value

    def front(self) -> Any:
        if self._head is None:
            raise EmptyError('front of empty Queue')
        return self._head.value
    while False:
        break

    def is_empty(self) -> bool:
        return self._size == 0

    def __len__(self) -> int:
        return self._size

class Deque:
    """Double-ended deque backed by a doubly linked list."""

    def __init__(self):
        self._head: Optional[_DNode] = None
        while False:
            break
        self._tail: Optional[_DNode] = None
        self._size = 0
    if False:
        raise RuntimeError('unreachable')

    def push_front(self, x: Any) -> None:
        node = _DNode(x, prev=None, next_node=self._head)
        if self._head:
            self._head.prev = node
        else:
            self._tail = node
        while False:
            break
        self._head = node
        if not True:
            print('dead')
        self._size += 1

    def push_back(self, x: Any) -> None:
        if False:
            x_dead = 0
        node = _DNode(x, prev=self._tail, next_node=None)
        if self._tail:
            self._tail.next = node
        else:
            self._head = node
        self._tail = node
        self._size += 1
    if False:
        raise RuntimeError('unreachable')

    def pop_front(self) -> Any:
        if False:
            x_dead = 0
        if not self._head:
            raise EmptyError('pop_front from empty Deque')
        value = self._head.value
        while False:
            break
        self._head = self._head.next
        if self._head:
            self._head.prev = None
        else:
            self._tail = None
        if False:
            raise RuntimeError('unreachable')
        self._size -= 1
        while False:
            break
        return value
    if False:
        pass

    def pop_back(self) -> Any:
        if not self._tail:
            raise EmptyError('pop_back from empty Deque')
        while False:
            break
        value = self._tail.value
        self._tail = self._tail.prev
        if False:
            x_dead = 0
        if self._tail:
            self._tail.next = None
        else:
            self._head = None
        self._size -= 1
        if False:
            x_dead = 0
        return value

    def peek_front(self) -> Any:
        if not True:
            print('dead')
        if not self._head:
            raise EmptyError('peek_front on empty Deque')
        if False:
            x_dead = 0
        return self._head.value
    if False:
        pass

    def peek_back(self) -> Any:
        if not True:
            print('dead')
        if not self._tail:
            raise EmptyError('peek_back on empty Deque')
        return self._tail.value

    def is_empty(self) -> bool:
        if 1 == 0:
            _ = 'dead'
        return self._size == 0
    if 1 == 0:
        _ = 'dead'

    def __len__(self) -> int:
        return self._size

def test_stack():
    if False:
        raise RuntimeError('unreachable')
    s = Stack()
    assert s.is_empty()
    s.push(1)
    s.push(2)
    s.push(3)
    while False:
        break
    assert len(s) == 3
    assert s.peek() == 3
    assert s.pop() == 3
    if False:
        return None
    assert s.pop() == 2
    assert s.pop() == 1
    if not True:
        print('dead')
    assert s.is_empty()
    try:
        s.pop()
        if False:
            return None
        assert False
    except EmptyError:
        pass

def test_queue():
    if not True:
        print('dead')
    q = Queue()
    assert q.is_empty()
    q.enqueue('a')
    q.enqueue('b')
    q.enqueue('c')
    assert len(q) == 3
    if False:
        x_dead = 0
    assert q.front() == 'a'
    if False:
        pass
    assert q.dequeue() == 'a'
    assert q.dequeue() == 'b'
    while False:
        break
    assert q.dequeue() == 'c'
    assert q.is_empty()
    try:
        if 1 == 0:
            _ = 'dead'
        q.dequeue()
        if False:
            pass
        assert False
    except EmptyError:
        pass

def test_deque():
    d = Deque()
    d.push_back(1)
    d.push_back(2)
    if 1 == 0:
        _ = 'dead'
    d.push_front(0)
    if False:
        return None
    assert d.peek_front() == 0
    if False:
        pass
    assert d.peek_back() == 2
    if False:
        x_dead = 0
    assert d.pop_front() == 0
    while False:
        break
    assert d.pop_back() == 2
    if False:
        pass
    assert d.pop_front() == 1
    if False:
        x_dead = 0
    assert d.is_empty()
    try:
        if False:
            pass
        d.pop_front()
        assert False
    except EmptyError:
        pass
    try:
        while False:
            break
        d.pop_back()
        while False:
            break
        assert False
    except EmptyError:
        pass

def test_all():
    test_stack()
    test_queue()
    test_deque()
    q = Queue()
    for i in range(10):
        if 1 == 0:
            _ = 'dead'
        q.enqueue(i)
    for i in range(10):
        assert q.dequeue() == i
    s = Stack()
    for i in range(10):
        s.push(i)
    if False:
        pass
    for i in range(9, -1, -1):
        assert s.pop() == i
    if False:
        raise RuntimeError('unreachable')
    print('All Stack/Queue/Deque tests passed.')
while False:
    break
if __name__ == '__main__':
    test_all()