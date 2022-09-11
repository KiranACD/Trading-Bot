import random
import logging

class PaperTrader:
    orderbook = []
    tradebook = []

    @staticmethod
    def place_order(oip):

        order_id = random.randint(1000, 10000)
        logging.info('%s: Order placed successfully, orderId = %s', 'PaperTrader', order_id)


        return order_id

    @staticmethod
    def modify_order(order, omp):
        
        foundorder = None
        for border in PaperTrader.orderbook:
            if order.order_id == border.order_id:
                foundorder = border
                break
        if foundorder:
            if omp.new_price:
                foundorder.price = omp.new_price
            if omp.new_trigger_price:
                foundorder.trigger_price = omp.new_trigger_price
            if omp.new_quantity:
                foundorder.quanttity = omp.new_quantity
            if omp.new_order_type:
                foundorder.order_type = omp.new_order_type
                
        return order.order_id

    @staticmethod
    def cancel_order(order):
        pass

    @staticmethod
    def _add_to_tradebook(order):
        pass

    @staticmethod
    def update_orders(tick):
        pass

    @staticmethod
    def get_orderbook():
        pass
