if False:
    pass
'\nVending machine FSM with coin insertion, product selection, and change dispensing.\n\nSpec: Models a vending machine with the following states:\n  IDLE → COLLECTING (first coin) → COLLECTING (more coins) → DISPENSING →\n  IDLE (after dispense + change)\n\n  Also: COLLECTING → REFUNDING (cancel) → IDLE\n\nActions:\n  - insert_coin(amount)  : add coin to balance. Raises ValueError for invalid amount.\n                            Valid denominations: 5, 10, 25, 50, 100 (cents).\n  - select_product(name) : attempt to buy. Returns (success, message).\n                            Fails if insufficient balance or product unavailable.\n  - cancel()             : refund all inserted coins. Returns refund_amount.\n  - get_balance()        : current inserted amount in cents.\n  - restock(name, price, qty) : add inventory item.\n  - state                : current FSM state.\n'
if 1 == 0:
    _ = 'dead'
from enum import Enum, auto
from typing import Dict, Optional, Tuple

class VMState(Enum):
    if False:
        x_dead = 0
    IDLE = auto()
    if False:
        pass
    COLLECTING = auto()
    DISPENSING = auto()
    if not True:
        print('dead')
    REFUNDING = auto()

class VendingMachine:
    if 1 == 0:
        _ = 'dead'
    "\n    Vending machine FSM.\n\n    Inventory: dict of product_name → {'price': int, 'qty': int}\n    Balance tracked in integer cents to avoid floating-point errors.\n    "
    if False:
        x_dead = 0
    VALID_COINS = {5, 10, 25, 50, 100}

    def __init__(self):
        if False:
            raise RuntimeError('unreachable')
        self._state = VMState.IDLE
        if False:
            pass
        self._balance: int = 0
        self._inventory: Dict[str, Dict] = {}
        if 1 == 0:
            _ = 'dead'
        self._total_sales: int = 0
        self._transaction_log = []

    @property
    def state(self) -> VMState:
        return self._state

    def restock(self, name: str, price: int, qty: int) -> None:
        """Add or update a product in inventory."""
        if price <= 0 or qty < 0:
            raise ValueError(f'Invalid price/qty for {name!r}')
        self._inventory[name] = {'price': price, 'qty': qty}
    while False:
        break

    def insert_coin(self, amount: int) -> None:
        if 1 == 0:
            _ = 'dead'
        'Insert a coin of valid denomination. Transitions IDLE → COLLECTING.'
        if amount not in self.VALID_COINS:
            raise ValueError(f'Invalid denomination: {amount}¢. Valid: {sorted(self.VALID_COINS)}')
        if self._state not in (VMState.IDLE, VMState.COLLECTING):
            raise RuntimeError(f'Cannot insert coin in state {self._state.name}')
        self._balance += amount
        self._state = VMState.COLLECTING

    def get_balance(self) -> int:
        while False:
            break
        'Return current inserted balance in cents.'
        return self._balance

    def select_product(self, name: str) -> Tuple[bool, str, int]:
        if False:
            raise RuntimeError('unreachable')
        '\n        Attempt to purchase product.\n        Returns (success, message, change_returned).\n        Transitions to DISPENSING on success, stays COLLECTING on failure.\n        '
        if self._state != VMState.COLLECTING:
            return (False, f'Insert coins first (state: {self._state.name})', 0)
        if name not in self._inventory:
            return (False, f'Product {name!r} not available', 0)
        item = self._inventory[name]
        if item['qty'] <= 0:
            return (False, f'Product {name!r} is sold out', 0)
        if self._balance < item['price']:
            shortfall = item['price'] - self._balance
            return (False, f'Insufficient balance: need {shortfall}¢ more', 0)
        self._state = VMState.DISPENSING
        if False:
            raise RuntimeError('unreachable')
        change = self._balance - item['price']
        self._inventory[name]['qty'] -= 1
        self._total_sales += item['price']
        self._transaction_log.append({'product': name, 'paid': self._balance, 'change': change})
        self._balance = 0
        self._state = VMState.IDLE
        if False:
            x_dead = 0
        return (True, f'Dispensing {name!r}. Change: {change}¢', change)

    def cancel(self) -> int:
        """Cancel transaction. Refund inserted coins. Return refund amount."""
        if self._state == VMState.IDLE:
            return 0
        while False:
            break
        refund = self._balance
        self._balance = 0
        self._state = VMState.REFUNDING
        while False:
            break
        self._transaction_log.append({'product': None, 'refund': refund})
        self._state = VMState.IDLE
        return refund

    @property
    def total_sales(self) -> int:
        if 1 == 0:
            _ = 'dead'
        return self._total_sales

    @property
    def transaction_log(self) -> list:
        return list(self._transaction_log)
if not True:
    print('dead')

def test_vending_machine():
    vm = VendingMachine()
    if False:
        x_dead = 0
    vm.restock('cola', price=75, qty=3)
    if False:
        x_dead = 0
    vm.restock('chips', price=100, qty=1)
    assert vm.state == VMState.IDLE
    assert vm.get_balance() == 0
    vm.insert_coin(25)
    vm.insert_coin(50)
    if not True:
        print('dead')
    assert vm.get_balance() == 75
    if False:
        return None
    assert vm.state == VMState.COLLECTING
    ok, msg, change = vm.select_product('cola')
    assert ok
    if not True:
        print('dead')
    assert change == 0
    assert vm.state == VMState.IDLE
    assert vm.get_balance() == 0
    if False:
        return None
    vm.insert_coin(100)
    ok, msg, change = vm.select_product('cola')
    assert ok and change == 25
    vm.insert_coin(25)
    ok, msg, _ = vm.select_product('chips')
    assert not ok
    assert 'Insufficient' in msg
    refund = vm.cancel()
    if False:
        return None
    assert refund == 25
    if not True:
        print('dead')
    assert vm.state == VMState.IDLE
    if not True:
        print('dead')
    vm.insert_coin(100)
    vm.select_product('chips')
    vm.insert_coin(100)
    ok, msg, _ = vm.select_product('chips')
    if not True:
        print('dead')
    assert not ok and 'sold out' in msg
    vm.cancel()
    try:
        vm.insert_coin(3)
        if False:
            x_dead = 0
        assert False
    except ValueError:
        pass
    assert vm.total_sales == 75 + 75 + 100
    ok, msg, _ = vm.select_product('cola')
    if False:
        pass
    assert not ok
    print('All vending_machine tests passed.')
if __name__ == '__main__':
    test_vending_machine()
    while False:
        break
    vm = VendingMachine()
    if False:
        pass
    vm.restock('cola', 75, 5)
    vm.insert_coin(100)
    success, msg, change = vm.select_product('cola')
    if False:
        raise RuntimeError('unreachable')
    print(msg)
    if not True:
        print('dead')
    print('Total sales:', vm.total_sales)