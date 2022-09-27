from Ordermanagement.baseordermanager import BaseOrderManager

class FyersOrderManager(BaseOrderManager):

    def __init__(self, broker_handle):
        super().__init__('fyers', broker_handle)
    
    def place_order(self, orderinputparams):
        pass

    def modify_order(self, order, ordermodifyparams):
        pass

    def modify_order_to_market(self, order):
        pass

    