import logging

from Ordermanagement.baseordermanager import BaseOrderManager
from Ordermanagement.order import Order
from Models.producttype import ProductType
from Models.ordertype import OrderType
from Models.direction import Direction
from Models.orderstatus import OrderStatus
from Utils.utils import get_epoch

class FyersOrderManager(BaseOrderManager):

    def __init__(self, broker_handle):
        super().__init__('fyers', broker_handle)
    
    def place_order(self, orderinputparams):
        fyers = self.broker_handle
        data = {
            'symbol':orderinputparams.tradingSymbol,
            'qty':orderinputparams.quantity,
            'type':self.convert_to_broker_order_type(orderinputparams.order_type),
            'side':self.convert_to_broker_direction_type(orderinputparams.direction),
            'productType':self.convert_to_broker_product_type(orderinputparams.product_type),
            'limitPrice':orderinputparams.price,
            'stopPrice':orderinputparams.trigger_price,
            'validity':'DAY',
            'disclosedQty':0,
            'offlineOrder':'False',
            'stopLoss':0,
            'takeProfit':0
        }
        try:
            order_details = fyers.place_order(data)
            message = order_details['message']
            order_id = order_details['id']
            
            order = Order(orderinputparams)
            order.order_id = order_id
            order.orderplacetimestamp = get_epoch()
            order.lastorderupdatetimestamp = get_epoch()
            order.message = message
            return order
        except Exception as e:
            logging.info('%s Order placement failed: %s', self.broker, str(e))

    def modify_order(self, order, ordermodifyparams):
        fyers = self.broker_handle
        logging.info('%s: Going to modify order with params %s', self.broker, ordermodifyparams)
        order_type = ordermodifyparams.new_order_type if ordermodifyparams.new_order_type else order.order_type
        new_price = ordermodifyparams.new_price if ordermodifyparams.new_price else order.price
        stop_price = ordermodifyparams.new_trigger_price if ordermodifyparams.new_trigger_price else order.trigger_price
        if stop_price:
            data = {
                'id':order.order_id,
                'type':order_type,
                'limitPrice':new_price,
                'stopPrice':stop_price
        }
        else:
            data = {
                'id':order.order_id,
                'type':order_type,
                'limitPrice':new_price
        }
        try:
            order_details = fyers.modify_order(data)
            message = order_details['message']
            order_id = order_details['id']
            logging.info('%s Order modified successfully for orderId = %s', self.broker, order_id)
            order.lastorderupdatetimestamp = get_epoch()
            order.message = message
            return order
        except Exception as e:
            logging.info('%s Order modify failed: %s', self.broker, str(e))
            raise Exception(str(e))

    def modify_order_to_market(self, order):
        fyers = self.broker_handle
        # self.cancel_order(order)

        # data = {
        #     'symbol'
        # }
        data = {
            'id':order.order_id,
            'type':2
        }
        try:
            order_details = fyers.modify_order(data)
            message = order_details['message']
            order_id = order_details['id']
            logging.info('%s Order modified successfully to market for orderId = %s', self.broker, order_id)
            order.lastorderupdatetimestamp = get_epoch()
            order.message = message
            return order
        except Exception as e:
            logging.info('%s Order modify to market failed: %s', self.broker, str(e))
            raise Exception(str(e))

    def cancel_order(self, order):
        fyers = self.broker_handle
        order_id = order.order_id
        try:
            fyers.cancel_order({'id':order_id})
        except Exception as e:
            logging.error('%s Order cancel failed: %s', self.broker, str(e))
            raise Exception(str(e))
    
    def fetch_and_update_all_order_details(self, orders):
        logging.info('%s Going to fetch order book', self.broker)
        fyers = self.broker_handle
        order_book = None
        try:
            order_book = fyers.orderbook()
        except Exception as e:
            logging.error('%s Failed to fetch order book', self.broker)
            return

        logging.info('%s Order book length = %d', self.broker, len(order_book))
        num_orders_updated = 0
        for b_order in order_book:
            found_order = None
            for order in orders:
                if order.order_id == b_order['id']:
                    found_order = order
                    break
                
            if found_order != None:
                logging.info('Found order for orderId %s', found_order.order_id)
                found_order.quantity = b_order['qty']
                found_order.filled_quantity = b_order['filledQty']
                found_order.pending_quantity = b_order['remainingQuantity']
                found_order.order_status = self.convert_orderstatus_to_apporderstatus(b_order['status'])
                if found_order.order_status == OrderStatus.CANCELLED and found_order.filled_quantity > 0:
                    # Consider this case as completed in our system as we cancel the order with pending qty when strategy stop timestamp reaches
                    found_order.order_status = OrderStatus.COMPLETED
                found_order.price = b_order['limitPrice']
                found_order.trigger_price = b_order['stopPrice']
                found_order.average_price = b_order['tradedPrice']
                logging.info('%s Updated order %s', self.broker, found_order)
                num_orders_updated += 1

        logging.info('%s: %d orders updated with broker order details', self.broker, num_orders_updated)

    def convert_to_broker_product_type(self, product_type):
        if product_type == ProductType.INTRADAY:
            return 'INTRADAY'
        elif product_type == ProductType.DERIVATIVE_POSITIONAL:
            return 'MARGIN'
        elif product_type == ProductType.EQUITY_POSITIONAL:
            return 'CNC'
        return None 

    def convert_to_broker_order_type(self, order_type):
        if order_type == OrderType.LIMIT:
            return 1
        elif order_type == OrderType.MARKET:
            return 2
        elif order_type == OrderType.SL_MARKET:
            return 3
        elif order_type == OrderType.SL_LIMIT:
            return 4
        return None

    def convert_to_broker_direction_type(self, direction):
        if direction == Direction.LONG:
            return 1
        elif direction == Direction.SHORT:
            return -1
        return None
    

    def convert_orderstatus_to_apporderstatus(self, status):
        if status == 1:
            return OrderStatus.CANCELLED
        elif status == 2:
            return OrderStatus.COMPLETE
        elif status == 4:
            return OrderStatus.VALIDATION_PENDING
        elif status == 5:
            return OrderStatus.REJECTED
        elif status == 6:
            return OrderStatus.OPEN
        return None
        

    