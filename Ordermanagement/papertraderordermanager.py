from ast import Or
import logging
import random
import datetime

from Ordermanagement.baseordermanager import BaseOrderManager
from Ordermanagement.order import Order
from Ordermanagement.ordermodifyparams import OrderModifyParams
from Instruments.instruments import Instruments
from PaperTrader.papertrader import PaperTrader
from Models.ordertype import OrderType
from Models.direction import Direction
from Models.orderstatus import OrderStatus
from HistoricalData.historicaldata import HistoricalData

from Utils.utils import get_epoch

class PaperTraderOrderManager(BaseOrderManager):
    def __init__(self, broker_handle):
        super().__init__('papertrader', broker_handle)
    
    def place_order(self, orderinputparams):
        logging.info('%s: Going to place order with params %s', self.broker, orderinputparams)
        order_id = PaperTrader.place_order(orderinputparams)
        logging.info('%s: Order placed successfully, orderId = %s', self.broker, order_id)
        order = Order(orderinputparams)
        order.order_id = order_id
        order.orderplacetimestamp = get_epoch()
        order.lastorderupdatetimestamp = get_epoch()
        return order
    
    def modify_order(self, order, ordermodifyparams):
        logging.info('%s: Going to modify order with params %s', self.broker, ordermodifyparams)
        order_id = PaperTrader.modify_order(order, ordermodifyparams)
        if order_id:
            logging.info('%s Order modified successfully for orderId = %s', self.broker, order_id)
            order.lastorderupdatetimestamp = get_epoch()
            return order
        logging.info('%s Order modify failed', self.broker)
        raise Exception(f'Order with order id {order.order_id} not modified because order not found')
    
    def modify_order_to_market(self, order):
        logging.info('%s: Going to modify order to ordertype market', self.broker)

        omp = OrderModifyParams()
        omp.new_order_type = OrderType.MARKET
        order_id = PaperTrader.modify_order(order, omp)
        if order_id:
            logging.info('%s Order modified successfully to ordertype market for orderId = %s', self.broker, order_id)
            order.lastorderupdatetimestamp = get_epoch()
            return order
        logging.info('%s Order modify to ordertype Market failed', self.broker)
        raise Exception(f'Order with order id {order.order_id} not modified to ordertype market because order not found')
    
    def cancel_order(self, order):
        logging.info('%s Going to cancel order %s', self.broker, order.order_id)
        order_id = PaperTrader.cancel_order(order)
        if order_id:
            logging.info('%s Order cancelled successfully, orderId = %s', self.broker, order_id)
            order.lastorderupdatetimestamp = get_epoch()
            return order
        logging.info('%s Order cancel failed', self.broker)
        raise Exception(f'Order with order id {order.order_id} not cancelled because order not found')
    
    def fetch_and_update_order_details(self, orders):
        num_orders_updated = 0
        orderbook = PaperTrader.get_orderbook()
        logging.info('%s Order book length = %d', self.broker, len(orderbook))
        for border in orderbook:
            foundorder = None
            for order in orders:
                if order.order_id == border.order_id:
                    foundorder = order
            
            if foundorder:
                logging.info('Found order for orderId %s', foundorder.order_id)
                foundorder.quantity = border.quantity
                foundorder.filled_quantity = border.filled_quantity
                foundorder.pending_quantity = border.pending_quantity
                foundorder.order_status = border.order_status
                if foundorder.order_status == OrderStatus.CANCELLED and foundorder.filled_quantity > 0:
                    foundorder.order_status = OrderStatus.COMPLETE
                foundorder.price = border.price
                foundorder.trigger_price = border.trigger_price
                foundorder.average_price = border.average_price
                logging.info('%s Updated order %s', self.broker, foundorder)
                num_orders_updated += 1
        logging.info('%s: %d orders updated with broker order details', self.broker, num_orders_updated)