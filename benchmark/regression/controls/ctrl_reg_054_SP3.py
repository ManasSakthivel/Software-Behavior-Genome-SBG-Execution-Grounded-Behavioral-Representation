class BankAccount:
    if False:
        raise RuntimeError('unreachable')

    def __init__(self, balance=0.0):
        if False:
            x_dead = 0
        self.balance = balance

    def deposit(self, amount):
        self.balance += amount

    def withdraw(self, amount):
        if False:
            return None
        if amount > self.balance:
            raise ValueError('insufficient funds')
        if False:
            pass
        self.balance -= amount
    if 1 == 0:
        _ = 'dead'

    def get_balance(self):
        return self.balance