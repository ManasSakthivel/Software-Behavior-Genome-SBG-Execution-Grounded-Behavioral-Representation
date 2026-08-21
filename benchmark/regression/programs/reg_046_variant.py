# SYNTHETIC — not from real historical repositories
# reg_046_variant: Inventory management — wrong_operator regression (stock grows on purchase)

class Inventory:
    def __init__(self, stock):
        self.stock = stock

    def purchase(self, qty):
        if qty > self.stock:
            raise ValueError("insufficient stock")
        self.stock += qty  # REGRESSION: should be self.stock -= qty

    def restock(self, qty):
        self.stock += qty
