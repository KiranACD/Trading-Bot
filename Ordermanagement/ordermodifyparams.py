class OrderModifyParams:
    def __init__(self):
        self.new_price = 0
        self.new_trigger_price = 0 # Applicable in case of SL order
        self.new_quantity = 0
        self.new_order_type = None # Ex: Can change LIMIT order to SL order or vice versa. Not supported by all brokers

    def __str__(self):
        return "newPrice=" + str(self.new_price) + ", newTriggerPrice=" + str(self.new_trigger_price) \
            + ", newQty=" + str(self.new_quantity) + ", newOrderType=" + str(self.new_order_type)