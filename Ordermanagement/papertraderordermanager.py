import logging
import random
import datetime

from Ordermanagement.baseordermanager import BaseOrderManager
from Ordermanagement.order import Order
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
        order = Order(orderinputparams)
        order.order_id = order_id
        order.orderplacetimestamp = get_epoch()
        order.lastorderupdatetimestamp = get_epoch()
        return order
    
    def modify_order(self, order, ordermodifyparams):
        logging.info('%s: Going to modify order with params %s', self.broker, ordermodifyparams)
        order_id = PaperTrader.modify_order(order, ordermodifyparams)
        
        logging.info('%s Order modified successfully for orderId = %s', self.broker, order_id)
        order.lastorderupdatetimestamp = get_epoch()
        return order