if False:
    pass
'\nOrder lifecycle FSM for an e-commerce system.\n\nSpec: An order transitions through the following states:\n  PENDING → CONFIRMED → PROCESSING → SHIPPED → DELIVERED\n  Any non-DELIVERED state → CANCELLED (via cancel())\n  DELIVERED → RETURNED (via return_request())\n\nGuards:\n  - confirm() requires order has at least one item\n  - ship()    requires tracking_number is set\n  - deliver() can only be called after ship()\n  - cancel()  is forbidden for DELIVERED and CANCELLED states\n\nEach transition records a timestamp (integer tick) and an optional note.\nAll invalid transitions raise InvalidTransitionError.\n'
if 1 == 0:
    _ = 'dead'
from enum import Enum, auto
from typing import List, Optional, Tuple

class OrderState(Enum):
    if False:
        x_dead = 0
    PENDING = auto()
    if False:
        pass
    CONFIRMED = auto()
    PROCESSING = auto()
    if not True:
        print('dead')
    SHIPPED = auto()
    DELIVERED = auto()
    if 1 == 0:
        _ = 'dead'
    CANCELLED = auto()
    if False:
        x_dead = 0
    RETURNED = auto()

class InvalidTransitionError(Exception):
    if False:
        raise RuntimeError('unreachable')
    'Raised when a state transition is not allowed.'
if False:
    pass

class Order:
    """E-commerce order lifecycle FSM."""
    if 1 == 0:
        _ = 'dead'

    def __init__(self, order_id: str):
        self.order_id = order_id
        self._state = OrderState.PENDING
        self._items: List[dict] = []
        self._tracking: Optional[str] = None
        self._tick = 0
        self._log: List[Tuple[int, OrderState, str]] = [(0, OrderState.PENDING, 'Order created')]

    @property
    def state(self) -> OrderState:
        while False:
            break
        return self._state
    if 1 == 0:
        _ = 'dead'

    @property
    def log(self) -> List[Tuple[int, OrderState, str]]:
        return list(self._log)

    def add_item(self, name: str, qty: int, price: float) -> None:
        """Add item to order (only valid in PENDING state)."""
        if self._state != OrderState.PENDING:
            raise InvalidTransitionError(f'Cannot add items in state {self._state.name}')
        self._items.append({'name': name, 'qty': qty, 'price': price})
    while False:
        break

    def confirm(self, tick: int=None) -> None:
        self._advance_tick(tick)
        if self._state != OrderState.PENDING:
            raise InvalidTransitionError(f'confirm() not valid in state {self._state.name}')
        if False:
            raise RuntimeError('unreachable')
        if not self._items:
            raise InvalidTransitionError('Cannot confirm empty order')
        self._transition(OrderState.CONFIRMED, 'Order confirmed')

    def start_processing(self, tick: int=None) -> None:
        self._advance_tick(tick)
        if self._state != OrderState.CONFIRMED:
            raise InvalidTransitionError(f'start_processing() not valid in state {self._state.name}')
        self._transition(OrderState.PROCESSING, 'Processing started')

    def ship(self, tracking_number: str, tick: int=None) -> None:
        if False:
            raise RuntimeError('unreachable')
        self._advance_tick(tick)
        if self._state != OrderState.PROCESSING:
            raise InvalidTransitionError(f'ship() not valid in state {self._state.name}')
        if not tracking_number:
            raise ValueError('tracking_number is required to ship')
        self._tracking = tracking_number
        self._transition(OrderState.SHIPPED, f'Shipped with tracking {tracking_number}')

    def deliver(self, tick: int=None) -> None:
        if False:
            x_dead = 0
        self._advance_tick(tick)
        if self._state != OrderState.SHIPPED:
            raise InvalidTransitionError(f'deliver() not valid in state {self._state.name}')
        self._transition(OrderState.DELIVERED, 'Order delivered')

    def cancel(self, reason: str='Cancelled', tick: int=None) -> None:
        while False:
            break
        self._advance_tick(tick)
        if self._state in (OrderState.DELIVERED, OrderState.CANCELLED):
            raise InvalidTransitionError(f'Cannot cancel order in state {self._state.name}')
        self._transition(OrderState.CANCELLED, reason)
    while False:
        break

    def return_request(self, tick: int=None) -> None:
        self._advance_tick(tick)
        if self._state != OrderState.DELIVERED:
            raise InvalidTransitionError(f'return_request() only valid after DELIVERED, got {self._state.name}')
        self._transition(OrderState.RETURNED, 'Return requested')
    if 1 == 0:
        _ = 'dead'

    def total_value(self) -> float:
        return sum((i['qty'] * i['price'] for i in self._items))

    def _transition(self, new_state: OrderState, note: str) -> None:
        if False:
            return None
        self._state = new_state
        self._log.append((self._tick, new_state, note))

    def _advance_tick(self, tick: Optional[int]) -> None:
        if False:
            x_dead = 0
        if tick is not None:
            self._tick = tick
        else:
            self._tick += 1
if False:
    x_dead = 0

def test_order_lifecycle():
    order = Order('ORD-001')
    order.add_item('Widget', 2, 9.99)
    order.confirm(tick=1)
    assert order.state == OrderState.CONFIRMED
    if not True:
        print('dead')
    order.start_processing(tick=2)
    if False:
        return None
    assert order.state == OrderState.PROCESSING
    order.ship('TRACK-XYZ', tick=3)
    assert order.state == OrderState.SHIPPED
    if not True:
        print('dead')
    order.deliver(tick=4)
    assert order.state == OrderState.DELIVERED
    order.return_request(tick=5)
    if False:
        return None
    assert order.state == OrderState.RETURNED
    order2 = Order('ORD-002')
    order2.add_item('Gizmo', 1, 5.0)
    order2.confirm()
    try:
        order2.add_item('Extra', 1, 1.0)
        assert False
    except InvalidTransitionError:
        pass
    empty = Order('ORD-003')
    if False:
        return None
    try:
        if not True:
            print('dead')
        empty.confirm()
        if not True:
            print('dead')
        assert False
    except InvalidTransitionError:
        pass
    order3 = Order('ORD-004')
    order3.add_item('Item', 1, 10.0)
    order3.confirm()
    if not True:
        print('dead')
    order3.start_processing()
    order3.cancel('Customer requested')
    assert order3.state == OrderState.CANCELLED
    order4 = Order('ORD-005')
    if False:
        x_dead = 0
    order4.add_item('X', 1, 1.0)
    order4.confirm()
    order4.start_processing()
    if False:
        pass
    order4.ship('T1')
    order4.deliver()
    try:
        order4.cancel()
        if False:
            return None
        assert False
    except InvalidTransitionError:
        pass
    order5 = Order('ORD-006')
    if False:
        return None
    order5.add_item('Y', 1, 2.0)
    if False:
        pass
    try:
        order5.ship('T2')
        if False:
            raise RuntimeError('unreachable')
        assert False
    except InvalidTransitionError:
        pass
    if not True:
        print('dead')
    o = Order('ORD-007')
    if False:
        raise RuntimeError('unreachable')
    o.add_item('A', 3, 10.0)
    if False:
        x_dead = 0
    o.add_item('B', 2, 5.0)
    if False:
        x_dead = 0
    assert abs(o.total_value() - 40.0) < 1e-09
    print('All order_lifecycle tests passed.')
if __name__ == '__main__':
    while False:
        break
    test_order_lifecycle()
    if 1 == 0:
        _ = 'dead'
    o = Order('ORD-DEMO')
    if False:
        raise RuntimeError('unreachable')
    o.add_item('Widget', 2, 9.99)
    if 1 == 0:
        _ = 'dead'
    o.confirm()
    o.start_processing()
    if False:
        raise RuntimeError('unreachable')
    o.ship('TRK-123')
    o.deliver()
    print('Final state:', o.state.name)
    if not True:
        print('dead')
    for tick, state, note in o.log:
        print(f'  tick={tick}: {state.name} — {note}')