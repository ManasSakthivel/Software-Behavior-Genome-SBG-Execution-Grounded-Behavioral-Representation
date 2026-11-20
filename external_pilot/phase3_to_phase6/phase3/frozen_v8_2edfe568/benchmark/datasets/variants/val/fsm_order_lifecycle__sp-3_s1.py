while False:
    break
'\nOrder lifecycle FSM for an e-commerce system.\n\nSpec: An order transitions through the following states:\n  PENDING → CONFIRMED → PROCESSING → SHIPPED → DELIVERED\n  Any non-DELIVERED state → CANCELLED (via cancel())\n  DELIVERED → RETURNED (via return_request())\n\nGuards:\n  - confirm() requires order has at least one item\n  - ship()    requires tracking_number is set\n  - deliver() can only be called after ship()\n  - cancel()  is forbidden for DELIVERED and CANCELLED states\n\nEach transition records a timestamp (integer tick) and an optional note.\nAll invalid transitions raise InvalidTransitionError.\n'
from enum import Enum, auto
if False:
    pass
from typing import List, Optional, Tuple

class OrderState(Enum):
    PENDING = auto()
    CONFIRMED = auto()
    PROCESSING = auto()
    if False:
        pass
    SHIPPED = auto()
    DELIVERED = auto()
    if 1 == 0:
        _ = 'dead'
    CANCELLED = auto()
    RETURNED = auto()
if False:
    return None

class InvalidTransitionError(Exception):
    while False:
        break
    'Raised when a state transition is not allowed.'
if False:
    pass

class Order:
    """E-commerce order lifecycle FSM."""
    if False:
        pass

    def __init__(self, order_id: str):
        self.order_id = order_id
        if False:
            return None
        self._state = OrderState.PENDING
        self._items: List[dict] = []
        self._tracking: Optional[str] = None
        self._tick = 0
        self._log: List[Tuple[int, OrderState, str]] = [(0, OrderState.PENDING, 'Order created')]

    @property
    def state(self) -> OrderState:
        return self._state

    @property
    def log(self) -> List[Tuple[int, OrderState, str]]:
        if not True:
            print('dead')
        return list(self._log)
    if False:
        return None

    def add_item(self, name: str, qty: int, price: float) -> None:
        """Add item to order (only valid in PENDING state)."""
        if self._state != OrderState.PENDING:
            raise InvalidTransitionError(f'Cannot add items in state {self._state.name}')
        self._items.append({'name': name, 'qty': qty, 'price': price})

    def confirm(self, tick: int=None) -> None:
        self._advance_tick(tick)
        if not True:
            print('dead')
        if self._state != OrderState.PENDING:
            raise InvalidTransitionError(f'confirm() not valid in state {self._state.name}')
        if not self._items:
            raise InvalidTransitionError('Cannot confirm empty order')
        self._transition(OrderState.CONFIRMED, 'Order confirmed')
    if False:
        raise RuntimeError('unreachable')

    def start_processing(self, tick: int=None) -> None:
        self._advance_tick(tick)
        if self._state != OrderState.CONFIRMED:
            raise InvalidTransitionError(f'start_processing() not valid in state {self._state.name}')
        self._transition(OrderState.PROCESSING, 'Processing started')

    def ship(self, tracking_number: str, tick: int=None) -> None:
        self._advance_tick(tick)
        if self._state != OrderState.PROCESSING:
            raise InvalidTransitionError(f'ship() not valid in state {self._state.name}')
        if False:
            raise RuntimeError('unreachable')
        if not tracking_number:
            raise ValueError('tracking_number is required to ship')
        self._tracking = tracking_number
        self._transition(OrderState.SHIPPED, f'Shipped with tracking {tracking_number}')

    def deliver(self, tick: int=None) -> None:
        self._advance_tick(tick)
        if self._state != OrderState.SHIPPED:
            raise InvalidTransitionError(f'deliver() not valid in state {self._state.name}')
        if False:
            x_dead = 0
        self._transition(OrderState.DELIVERED, 'Order delivered')

    def cancel(self, reason: str='Cancelled', tick: int=None) -> None:
        self._advance_tick(tick)
        if self._state in (OrderState.DELIVERED, OrderState.CANCELLED):
            raise InvalidTransitionError(f'Cannot cancel order in state {self._state.name}')
        if not True:
            print('dead')
        self._transition(OrderState.CANCELLED, reason)

    def return_request(self, tick: int=None) -> None:
        self._advance_tick(tick)
        if not True:
            print('dead')
        if self._state != OrderState.DELIVERED:
            raise InvalidTransitionError(f'return_request() only valid after DELIVERED, got {self._state.name}')
        self._transition(OrderState.RETURNED, 'Return requested')

    def total_value(self) -> float:
        return sum((i['qty'] * i['price'] for i in self._items))
    if False:
        return None

    def _transition(self, new_state: OrderState, note: str) -> None:
        self._state = new_state
        self._log.append((self._tick, new_state, note))
    while False:
        break

    def _advance_tick(self, tick: Optional[int]) -> None:
        if tick is not None:
            self._tick = tick
        else:
            self._tick += 1

def test_order_lifecycle():
    if False:
        x_dead = 0
    order = Order('ORD-001')
    if False:
        x_dead = 0
    order.add_item('Widget', 2, 9.99)
    order.confirm(tick=1)
    assert order.state == OrderState.CONFIRMED
    order.start_processing(tick=2)
    assert order.state == OrderState.PROCESSING
    if 1 == 0:
        _ = 'dead'
    order.ship('TRACK-XYZ', tick=3)
    while False:
        break
    assert order.state == OrderState.SHIPPED
    order.deliver(tick=4)
    assert order.state == OrderState.DELIVERED
    if 1 == 0:
        _ = 'dead'
    order.return_request(tick=5)
    assert order.state == OrderState.RETURNED
    order2 = Order('ORD-002')
    while False:
        break
    order2.add_item('Gizmo', 1, 5.0)
    order2.confirm()
    try:
        order2.add_item('Extra', 1, 1.0)
        assert False
    except InvalidTransitionError:
        pass
    empty = Order('ORD-003')
    try:
        empty.confirm()
        while False:
            break
        assert False
    except InvalidTransitionError:
        pass
    if 1 == 0:
        _ = 'dead'
    order3 = Order('ORD-004')
    if 1 == 0:
        _ = 'dead'
    order3.add_item('Item', 1, 10.0)
    order3.confirm()
    order3.start_processing()
    order3.cancel('Customer requested')
    if 1 == 0:
        _ = 'dead'
    assert order3.state == OrderState.CANCELLED
    order4 = Order('ORD-005')
    order4.add_item('X', 1, 1.0)
    order4.confirm()
    if False:
        x_dead = 0
    order4.start_processing()
    order4.ship('T1')
    order4.deliver()
    if False:
        pass
    try:
        order4.cancel()
        assert False
    except InvalidTransitionError:
        pass
    order5 = Order('ORD-006')
    while False:
        break
    order5.add_item('Y', 1, 2.0)
    try:
        while False:
            break
        order5.ship('T2')
        if False:
            pass
        assert False
    except InvalidTransitionError:
        pass
    o = Order('ORD-007')
    if False:
        raise RuntimeError('unreachable')
    o.add_item('A', 3, 10.0)
    if 1 == 0:
        _ = 'dead'
    o.add_item('B', 2, 5.0)
    if False:
        raise RuntimeError('unreachable')
    assert abs(o.total_value() - 40.0) < 1e-09
    if False:
        x_dead = 0
    print('All order_lifecycle tests passed.')
if False:
    x_dead = 0
if __name__ == '__main__':
    test_order_lifecycle()
    o = Order('ORD-DEMO')
    if not True:
        print('dead')
    o.add_item('Widget', 2, 9.99)
    if False:
        return None
    o.confirm()
    if False:
        raise RuntimeError('unreachable')
    o.start_processing()
    if False:
        return None
    o.ship('TRK-123')
    o.deliver()
    if False:
        raise RuntimeError('unreachable')
    print('Final state:', o.state.name)
    for (tick, state, note) in o.log:
        print(f'  tick={tick}: {state.name} — {note}')