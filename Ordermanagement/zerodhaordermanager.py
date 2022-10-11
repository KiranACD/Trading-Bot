import logging

from Ordermanagement.baseordermanager import BaseOrderManager
from Ordermanagement.order import Order
from Models.producttype import ZerodhaProductType
from Models.ordertype import OrderType
from Models.direction import Direction
from Models.orderstatus import OrderStatus
from Utils.utils import get_epoch

class ZerodhaOrderManager(BaseOrderManager):
    def __init__(self, broker_handle):
        super().__init__("zerodha", broker_handle)

    def place_order(self, orderinputparams):
        logging.info('%s: Going to place order with params %s', self.broker, orderinputparams)
        kite = self.broker_handle
        try:
            order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NFO if orderinputparams.isFnO == True else kite.EXCHANGE_NSE,
            tradingsymbol=orderinputparams.tradingSymbol,
            transaction_type=self.convertToBrokerDirection(orderinputparams.direction),
            quantity=orderinputparams.quantity,
            price=orderinputparams.price,
            trigger_price=orderinputparams.trigger_price,
            product=self.convertToBrokerProductType(orderinputparams.product_type),
            order_type=self.convertToBrokerOrderType(orderinputparams.order_type))
            logging.info('%s: Order placed successfully, orderId = %s', self.broker, order_id)
            order = Order(orderinputparams)
            order.order_id = order_id
            order.orderplacetimestamp = get_epoch()
            order.lastorderupdatetimestamp = get_epoch()
            return order
        except Exception as e:
            logging.info('%s Order placement failed: %s', self.broker, str(e))
            raise Exception(str(e))

    def modify_order(self, order, ordermodifyparams):
        logging.info('%s: Going to modify order with params %s', self.broker, ordermodifyparams)
        kite = self.broker_handle
        try:
            order_id = kite.modify_order(
            variety=kite.VARIETY_REGULAR,
            order_id=order.order_id,
            quantity=ordermodifyparams.new_quantity if ordermodifyparams.new_quantity > 0 else None,
            price=ordermodifyparams.new_price if ordermodifyparams.new_price > 0 else None,
            trigger_price=ordermodifyparams.new_trigger_price if ordermodifyparams.new_trigger_price > 0 else None,
            order_type=ordermodifyparams.new_order_type if ordermodifyparams.new_order_type != None else None)

            logging.info('%s Order modified successfully for orderId = %s', self.broker, order_id)
            order.lastorderupdatetimestamp = get_epoch()
            return order
        except Exception as e:
            logging.info('%s Order modify failed: %s', self.broker, str(e))
            raise Exception(str(e))

    def modify_order_to_market(self, order):
        logging.info('%s: Going to modify order with params %s', self.broker)
        kite = self.broker_handle
        try:
            order_id = kite.modify_order(
            variety=kite.VARIETY_REGULAR,
            order_id=order.order_id,
            order_type=kite.ORDER_TYPE_MARKET)

            logging.info('%s Order modified successfully to MARKET for orderId = %s', self.broker, order_id)
            order.lastorderupdatetimestamp = get_epoch()
            return order
        except Exception as e:
            logging.info('%s Order modify to market failed: %s', self.broker, str(e))
            raise Exception(str(e))

    def cancel_order(self, order):
        logging.info('%s Going to cancel order %s', self.broker, order.order_id)
        kite = self.broker_handle
        try:
            order_id = kite.cancel_order(
            variety=kite.VARIETY_REGULAR,
            order_id=order.order_id)

            logging.info('%s Order cancelled successfully, orderId = %s', self.broker, order_id)
            order.lastorderupdatetimestamp = get_epoch()
            return order
        except Exception as e:
            logging.info('%s Order cancel failed: %s', self.broker, str(e))
            raise Exception(str(e))

    def fetch_and_update_all_order_details(self, orders):
        logging.info('%s Going to fetch order book', self.broker)
        kite = self.broker_handle
        order_book = None
        try:
            order_book = kite.orders()
        except Exception as e:
            logging.error('%s Failed to fetch order book', self.broker)
            return

        logging.info('%s Order book length = %d', self.broker, len(order_book))
        num_orders_updated = 0
        for b_order in order_book:
            found_order = None
            for order in orders:
                if order.order_id == b_order['order_id']:
                    found_order = order
                    break
                
            if found_order != None:
                logging.info('Found order for orderId %s', found_order.order_id)
                found_order.quantity = b_order['quantity']
                found_order.filled_quantity = b_order['filled_quantity']
                found_order.pending_quantity = b_order['pending_quantity']
                found_order.order_status = b_order['status']
                if found_order.order_status == OrderStatus.CANCELLED and found_order.filled_quantity > 0:
                    # Consider this case as completed in our system as we cancel the order with pending qty when strategy stop timestamp reaches
                    found_order.order_status = OrderStatus.COMPLETED
                found_order.price = b_order['price']
                found_order.trigger_price = b_order['trigger_price']
                found_order.average_price = b_order['average_price']
                logging.info('%s Updated order %s', self.broker, found_order)
                num_orders_updated += 1

        logging.info('%s: %d orders updated with broker order details', self.broker, num_orders_updated)

    def convert_to_broker_product_type(self, product_type):
        kite = self.broker_handle
        if product_type == ZerodhaProductType.MIS:
            return kite.PRODUCT_MIS
        elif product_type == ZerodhaProductType.NRML:
            return kite.PRODUCT_NRML
        elif product_type == ZerodhaProductType.CNC:
            return kite.PRODUCT_CNC
        return None 

    def convert_to_broker_order_type(self, order_type):
        kite = self.broker_handle
        if order_type == OrderType.LIMIT:
            return kite.ORDER_TYPE_LIMIT
        elif order_type == OrderType.MARKET:
            return kite.ORDER_TYPE_MARKET
        elif order_type == OrderType.SL_MARKET:
            return kite.ORDER_TYPE_SLM
        elif order_type == OrderType.SL_LIMIT:
            return kite.ORDER_TYPE_SL
        return None

    def convert_to_broker_direction_type(self, direction):
        kite = self.broker_handle
        if direction == Direction.LONG:
            return kite.TRANSACTION_TYPE_BUY
        elif direction == Direction.SHORT:
            return kite.TRANSACTION_TYPE_SELL
        return None
