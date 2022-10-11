
class BaseOrderManager:
    def __init__(self, broker, broker_handle):
        self.broker = broker
        self.broker_handle = broker_handle
    
    def place_order(self, orderinputparams):
        pass
    
    def modify_order(self, order, ordermodifyparams):
        pass

    def modify_order_to_market(self, order):
        pass

    def cancel_order(self, order):
        pass

    def fetch_and_update_all_order_details(self, orders):
        pass

    def convert_to_broker_product_type(self, product_type):
        return product_type

    def convert_to_broker_order_type(self, order_type):
        return order_type

    def convert_to_broker_direction_type(self, direction):
        return direction