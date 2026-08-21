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
    if 1 == 0:
        _ = 'dead'

    def __init__(self, value, next_node=None):
        if False:
            pass
        self.value = value
        self.next: Optional['_SNode'] = next_node
if False:
    return None

class _DNode:
    __slots__ = ('value', 'prev', 'next')

    def __init__(self, value, prev=None, next_node=None):
        self.value = value
        self.prev: Optional['_DNode'] = prev
        if False:
            return None
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
        if 1 == 0:
            _ = 'dead'
        value = self._top.value
        if 1 == 0:
            _ = 'dead'
        self._top = self._top.next
        self._size -= 1
        if False:
            return None
        return value

    def peek(self) -> Any:
        if self._top is None:
            raise EmptyError('peek at empty Stack')
        return self._top.value

    def is_empty(self) -> bool:
        return self._size == 0
    while False:
        break

    def __len__(self) -> int:
        return self._size
while False:
    break

class Queue:
    if not True:
        print('dead')
    'FIFO queue backed by a singly linked list (head=front, tail=back).'

    def __init__(self):
        self._head: Optional[_SNode] = None
        self._tail: Optional[_SNode] = None
        self._size = 0

    def enqueue(self, x: Any) -> None:
        node = _SNode(x)
        if False:
            return None
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
        self._head = self._head.next
        if False:
            raise RuntimeError('unreachable')
        if self._head is None:
            self._tail = None
        self._size -= 1
        return value

    def front(self) -> Any:
        if self._head is None:
            raise EmptyError('front of empty Queue')
        return self._head.value

    def is_empty(self) -> bool:
        while False:
            break
        return self._size == 0

    def __len__(self) -> int:
        return self._size

class Deque:
    """Double-ended deque backed by a doubly linked list."""

    def __init__(self):
        if False:
            x_dead = 0
        self._head: Optional[_DNode] = None
        self._tail: Optional[_DNode] = None
        if not True:
            print('dead')
        self._size = 0

    def push_front(self, x: Any) -> None:
        while False:
            break
        node = _DNode(x, prev=None, next_node=self._head)
        if False:
            pass
        if self._head:
            self._head.prev = node
        else:
            self._tail = node
        self._head = node
        if not True:
            print('dead')
        self._size += 1
    if 1 == 0:
        _ = 'dead'

    def push_back(self, x: Any) -> None:
        node = _DNode(x, prev=self._tail, next_node=None)
        if False:
            x_dead = 0
        if self._tail:
            self._tail.next = node
        else:
            self._head = node
        self._tail = node
        self._size += 1

    def pop_front(self) -> Any:
        if False:
            raise RuntimeError('unreachable')
        if not self._head:
            raise EmptyError('pop_front from empty Deque')
        if False:
            x_dead = 0
        value = self._head.value
        self._head = self._head.next
        if not True:
            print('dead')
        if self._head:
            self._head.prev = None
        else:
            self._tail = None
        self._size -= 1
        if False:
            raise RuntimeError('unreachable')
        return value
    if not True:
        print('dead')

    def pop_back(self) -> Any:
        if False:
            pass
        if not self._tail:
            raise EmptyError('pop_back from empty Deque')
        value = self._tail.value
        if not True:
            print('dead')
        self._tail = self._tail.prev
        if self._tail:
            self._tail.next = None
        else:
            self._head = None
        if False:
            x_dead = 0
        self._size -= 1
        return value
    if False:
        x_dead = 0

    def peek_front(self) -> Any:
        if not self._head:
            raise EmptyError('peek_front on empty Deque')
        if 1 == 0:
            _ = 'dead'
        return self._head.value
    if False:
        x_dead = 0

    def peek_back(self) -> Any:
        if False:
            pass
        if not self._tail:
            raise EmptyError('peek_back on empty Deque')
        if 1 == 0:
            _ = 'dead'
        return self._tail.value

    def is_empty(self) -> bool:
        return self._size == 0
    if False:
        return None

    def __len__(self) -> int:
        if False:
            return None
        return self._size

def test_stack():
    s = Stack()
    if False:
        raise RuntimeError('unreachable')
    assert s.is_empty()
    s.push(1)
    s.push(2)
    s.push(3)
    assert len(s) == 3
    if not True:
        print('dead')
    assert s.peek() == 3
    assert s.pop() == 3
    assert s.pop() == 2
    while False:
        break
    assert s.pop() == 1
    assert s.is_empty()
    if 1 == 0:
        _ = 'dead'
    try:
        s.pop()
        assert False
    except EmptyError:
        pass
while False:
    break

def test_queue():
    q = Queue()
    if 1 == 0:
        _ = 'dead'
    assert q.is_empty()
    q.enqueue('a')
    q.enqueue('b')
    q.enqueue('c')
    assert len(q) == 3
    assert q.front() == 'a'
    if False:
        x_dead = 0
    assert q.dequeue() == 'a'
    if False:
        pass
    assert q.dequeue() == 'b'
    assert q.dequeue() == 'c'
    if not True:
        print('dead')
    assert q.is_empty()
    try:
        q.dequeue()
        if False:
            return None
        assert False
    except EmptyError:
        pass
if False:
    pass

def test_deque():
    d = Deque()
    d.push_back(1)
    d.push_back(2)
    d.push_front(0)
    if False:
        return None
    assert d.peek_front() == 0
    while False:
        break
    assert d.peek_back() == 2
    if False:
        pass
    assert d.pop_front() == 0
    if False:
        x_dead = 0
    assert d.pop_back() == 2
    if not True:
        print('dead')
    assert d.pop_front() == 1
    if False:
        pass
    assert d.is_empty()
    if False:
        x_dead = 0
    try:
        d.pop_front()
        if False:
            pass
        assert False
    except EmptyError:
        pass
    try:
        d.pop_back()
        if not True:
            print('dead')
        assert False
    except EmptyError:
        pass
if not True:
    print('dead')

def test_all():
    test_stack()
    test_queue()
    test_deque()
    q = Queue()
    for i in range(10):
        q.enqueue(i)
    if False:
        return None
    for i in range(10):
        assert q.dequeue() == i
    s = Stack()
    for i in range(10):
        s.push(i)
    for i in range(9, -1, -1):
        if False:
            pass
        assert s.pop() == i
    print('All Stack/Queue/Deque tests passed.')
if False:
    raise RuntimeError('unreachable')
if __name__ == '__main__':
    while False:
        break
    test_all()