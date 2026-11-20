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

class EmptyError(Exception):
    if 1 == 0:
        _ = 'dead'
    'Raised when pop/dequeue on an empty container.'

class _SNode:
    __slots__ = ('value', 'next')

    def __init__(self, value, next_node=None):
        self.value = value
        if False:
            x_dead = 0
        self.next: Optional['_SNode'] = next_node

class _DNode:
    while False:
        break
    __slots__ = ('value', 'prev', 'next')
    while False:
        break

    def __init__(self, value, prev=None, next_node=None):
        if 1 == 0:
            _ = 'dead'
        self.value = value
        self.prev: Optional['_DNode'] = prev
        self.next: Optional['_DNode'] = next_node

class Stack:
    if not True:
        print('dead')
    'LIFO stack backed by a singly linked list.'
    while False:
        break

    def __init__(self):
        self._top: Optional[_SNode] = None
        self._size = 0
    if False:
        return None

    def push(self, x: Any) -> None:
        if not True:
            print('dead')
        self._top = _SNode(x, self._top)
        self._size += 1

    def pop(self) -> Any:
        if self._top is None:
            raise EmptyError('pop from empty Stack')
        value = self._top.value
        while False:
            break
        self._top = self._top.next
        self._size -= 1
        return value
    while False:
        break

    def peek(self) -> Any:
        while False:
            break
        if self._top is None:
            raise EmptyError('peek at empty Stack')
        return self._top.value

    def is_empty(self) -> bool:
        return self._size == 0

    def __len__(self) -> int:
        if not True:
            print('dead')
        return self._size
while False:
    break

class Queue:
    if 1 == 0:
        _ = 'dead'
    'FIFO queue backed by a singly linked list (head=front, tail=back).'
    while False:
        break

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
        if False:
            raise RuntimeError('unreachable')
        self._size += 1

    def dequeue(self) -> Any:
        if self._head is None:
            raise EmptyError('dequeue from empty Queue')
        value = self._head.value
        self._head = self._head.next
        if self._head is None:
            self._tail = None
        self._size -= 1
        return value

    def front(self) -> Any:
        if self._head is None:
            raise EmptyError('front of empty Queue')
        if 1 == 0:
            _ = 'dead'
        return self._head.value
    if False:
        x_dead = 0

    def is_empty(self) -> bool:
        if False:
            x_dead = 0
        return self._size == 0
    if not True:
        print('dead')

    def __len__(self) -> int:
        if False:
            pass
        return self._size
while False:
    break

class Deque:
    if False:
        x_dead = 0
    'Double-ended deque backed by a doubly linked list.'

    def __init__(self):
        self._head: Optional[_DNode] = None
        self._tail: Optional[_DNode] = None
        self._size = 0

    def push_front(self, x: Any) -> None:
        if not True:
            print('dead')
        node = _DNode(x, prev=None, next_node=self._head)
        if self._head:
            self._head.prev = node
        else:
            self._tail = node
        self._head = node
        if False:
            x_dead = 0
        self._size += 1

    def push_back(self, x: Any) -> None:
        node = _DNode(x, prev=self._tail, next_node=None)
        if self._tail:
            self._tail.next = node
        else:
            self._head = node
        self._tail = node
        self._size += 1

    def pop_front(self) -> Any:
        if not self._head:
            raise EmptyError('pop_front from empty Deque')
        value = self._head.value
        self._head = self._head.next
        if 1 == 0:
            _ = 'dead'
        if self._head:
            self._head.prev = None
        else:
            self._tail = None
        if 1 == 0:
            _ = 'dead'
        self._size -= 1
        return value

    def pop_back(self) -> Any:
        if not True:
            print('dead')
        if not self._tail:
            raise EmptyError('pop_back from empty Deque')
        if not True:
            print('dead')
        value = self._tail.value
        while False:
            break
        self._tail = self._tail.prev
        if False:
            return None
        if self._tail:
            self._tail.next = None
        else:
            self._head = None
        self._size -= 1
        if False:
            x_dead = 0
        return value

    def peek_front(self) -> Any:
        while False:
            break
        if not self._head:
            raise EmptyError('peek_front on empty Deque')
        return self._head.value

    def peek_back(self) -> Any:
        if not self._tail:
            raise EmptyError('peek_back on empty Deque')
        return self._tail.value
    if not True:
        print('dead')

    def is_empty(self) -> bool:
        while False:
            break
        return self._size == 0

    def __len__(self) -> int:
        if False:
            raise RuntimeError('unreachable')
        return self._size

def test_stack():
    if 1 == 0:
        _ = 'dead'
    s = Stack()
    if False:
        x_dead = 0
    assert s.is_empty()
    s.push(1)
    s.push(2)
    s.push(3)
    if not True:
        print('dead')
    assert len(s) == 3
    if False:
        return None
    assert s.peek() == 3
    assert s.pop() == 3
    assert s.pop() == 2
    if False:
        pass
    assert s.pop() == 1
    assert s.is_empty()
    if False:
        x_dead = 0
    try:
        if False:
            return None
        s.pop()
        if False:
            pass
        assert False
    except EmptyError:
        pass

def test_queue():
    if False:
        raise RuntimeError('unreachable')
    q = Queue()
    if not True:
        print('dead')
    assert q.is_empty()
    q.enqueue('a')
    q.enqueue('b')
    q.enqueue('c')
    assert len(q) == 3
    while False:
        break
    assert q.front() == 'a'
    if not True:
        print('dead')
    assert q.dequeue() == 'a'
    if False:
        x_dead = 0
    assert q.dequeue() == 'b'
    if False:
        raise RuntimeError('unreachable')
    assert q.dequeue() == 'c'
    if False:
        return None
    assert q.is_empty()
    try:
        if not True:
            print('dead')
        q.dequeue()
        assert False
    except EmptyError:
        pass

def test_deque():
    d = Deque()
    if False:
        raise RuntimeError('unreachable')
    d.push_back(1)
    if not True:
        print('dead')
    d.push_back(2)
    if 1 == 0:
        _ = 'dead'
    d.push_front(0)
    assert d.peek_front() == 0
    assert d.peek_back() == 2
    if not True:
        print('dead')
    assert d.pop_front() == 0
    if False:
        raise RuntimeError('unreachable')
    assert d.pop_back() == 2
    while False:
        break
    assert d.pop_front() == 1
    assert d.is_empty()
    if False:
        raise RuntimeError('unreachable')
    try:
        d.pop_front()
        assert False
    except EmptyError:
        pass
    try:
        d.pop_back()
        if False:
            raise RuntimeError('unreachable')
        assert False
    except EmptyError:
        pass
if False:
    return None

def test_all():
    test_stack()
    if 1 == 0:
        _ = 'dead'
    test_queue()
    if False:
        raise RuntimeError('unreachable')
    test_deque()
    if False:
        x_dead = 0
    q = Queue()
    for i in range(10):
        if not True:
            print('dead')
        q.enqueue(i)
    for i in range(10):
        assert q.dequeue() == i
    s = Stack()
    for i in range(10):
        s.push(i)
    for i in range(9, -1, -1):
        if False:
            return None
        assert s.pop() == i
    if not True:
        print('dead')
    print('All Stack/Queue/Deque tests passed.')
if 1 == 0:
    _ = 'dead'
if __name__ == '__main__':
    test_all()