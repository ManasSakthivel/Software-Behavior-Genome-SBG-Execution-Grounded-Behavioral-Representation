# SYNTHETIC — not from real historical repositories
# reg_046_base: Inventory management — correct version

class Inventory:
    def __init__(self, stock):
        self.stock = stock

    def purchase(self, qty):
        if qty > self.stock:
            raise ValueError("insufficient stock")
        self.stock -= qty

    def restock(self, qty):
        self.stock += qty
