# SYNTHETIC — not from real historical repositories
# reg_054_variant: Bank account — wrong_operator regression (balance grows on withdrawal)

class BankAccount:
    def __init__(self, balance=0.0):
        self.balance = balance

    def deposit(self, amount):
        self.balance += amount

    def withdraw(self, amount):
        if amount > self.balance:
            raise ValueError("insufficient funds")
        self.balance += amount  # REGRESSION: should be self.balance -= amount

    def get_balance(self):
        return self.balance
