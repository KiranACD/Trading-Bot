import logging
import random
import datetime

from Ordermanagement.baseordermanager import BaseOrderManager
from Ordermanagement.order import Order
from Instruments.instruments import Instruments

from Models.ordertype import OrderType
from Models.direction import Direction
from Models.orderstatus import OrderStatus
from HistoricalData.historicaldata import HistoricalData

from Utils.utils import get_epoch

class PaperTradeManager(BaseOrderManager):
    def __init__(self, broker_handle):
        super().__init__('papertrader', broker_handle)
        self.order_book = {}
    
    def add_in_order_book(self, order):
        self.order_book[order.order_id] = order

    def place_order(self, orderinputparams):
        logging.info('%s: Going to place order with params %s', self.broker, orderinputparams)

        order_id = random.randint(1000, 10000)
        logging.info('%s: Order placed successfully, orderId = %s', self.broker, order_id)

        order = Order(orderinputparams)
        order.order_id = order_id
        order.orderplacetimestamp = get_epoch()
        order.lastorderupdatetimestamp = get_epoch()
        self.add_in_order_book(order)
        return order
    
    def modify_order(self, order, ordermodifyparams):
        logging.info('%s: Going to modify order with params %s', self.broker, ordermodifyparams)
        order_id = order.order_id
        found_order = self.order_book[order_id]
        if found_order.order_ == 'sl_order':
            if ordermodifyparams.new_price:
                found_order.price = ordermodifyparams.new_price
            elif ordermodifyparams.new_trigger_price:
                found_order.trigger_price = ordermodifyparams.new_trigger_price
        logging.info('%s Order modified successfully for orderId = %s', self.broker, order_id)
        order.lastorderupdatetimestamp = get_epoch()
        return order
    
    def modify_order_to_market(self, order):
        logging.info('%s: Going to modify order with params %s', self.broker)
        order_id = order.order_id
        logging.info('%s Order modified successfully to MARKET for orderId = %s', self.broker, order_id)
        order.lastorderupdatetimestamp = get_epoch()
    
    def cancel_order(self, order):
        logging.info('%s Going to cancel order %s', self.broker, order.order_id)
        order_id = order.order_id
        self.order_book.pop(order_id)
        logging.info('%s Order cancelled successfully, orderId = %s', self.broker, order_id)
        order.lastorderupdatetimestamp = get_epoch()
    
    def fetch_and_update_all_order_details(self, orders):
        logging.info('%s Going to fetch order book', self.broker)
        order_book = None
        try:
            order_book = self.order_book
        except Exception as e:
            logging.error('%s Failed to fetch order book', self.broker)
            return

        logging.info('%s Order book length = %d', self.broker, len(order_book))
        num_orders_updated = 0
        for b_order in order_book:
            found_order = None
            for order in orders:
                if order.order_id == b_order:
                    found_order = order
                    break
                
            if found_order:
                logging.info('Found order for orderId %s', found_order.order_id)
                if found_order.order_ == 'sl_order':
                    # check if sl hit.
                    sl_hit = 0
                    token = Instruments.get_zerodha_instrument_token(found_order.tradingsymbol)
                    if token is None:
                        logging.error(f'Could not find token for order with id {str(found_order.id)} and symbol {found_order.tradingsymbol}')
                        continue
                    data = HistoricalData.get_historical_data(token, datetime.datetime.today(), datetime.datetime.today(), 'minute')
                    if data is None:
                        logging.error(f'Could not fetch historical data for order with id {str(found_order.id)} and symbol {found_order.tradingsymbol}')
                        continue
                    start_time = datetime.datetime.fromtimestamp(found_order.orderplacetimestamp)
                    data = data[data['date'] >= start_time]
                    if found_order.direction == Direction.LONG:
                        price = data['close'].max()
                        if price > found_order.trigger_price:
                            sl_hit = 1
                    else:
                        price = data['close'].min()
                        if price < found_order.trigger_price:
                            sl_hit = 1
                    if sl_hit == 1:
                        found_order.quantity = order_book[b_order].quantity
                        found_order.filled_quantity = order_book[b_order].quantity
                        # found_order.pending_quantity = order_book[b_order].pending_quantity
                        found_order.order_status = OrderStatus.COMPLETE
                    
                        found_order.price = order_book[b_order].trigger_price
                        found_order.trigger_price = order_book[b_order].trigger_price
                        found_order.average_price = order_book[b_order].price
                        logging.info('%s Updated order %s', self.broker, found_order)
                    else:
                        found_order.quantity = order_book[b_order].quantity
                        found_order.filled_quantity = 0
                        found_order.pending_quantity = order_book[b_order].quantity
                        found_order.order_status = OrderStatus.OPEN
                    
                        found_order.price = order_book[b_order].price
                        found_order.trigger_price = order_book[b_order].trigger_price
                        found_order.average_price = order_book[b_order].average_price
                        logging.info('%s Updated order %s', self.broker, found_order)
                    
                    num_orders_updated += 1
                
                if found_order.order_ == 'target_order':
                    target_hit = 0
                    token = Instruments.get_zerodha_instrument_token(found_order.tradingsymbol)
                    if token is None:
                        logging.error(f'Could not find token for order with id {str(found_order.id)} and symbol {found_order.tradingsymbol}')
                        continue
                    data = HistoricalData.get_historical_data(token, datetime.datetime.today(), datetime.datetime.today(), 'minute')
                    if data is None:
                        logging.error(f'Could not fetch historical data for order with id {str(found_order.id)} and symbol {found_order.tradingsymbol}')
                        continue
                    start_time = datetime.datetime.fromtimestamp(found_order.orderplacetimestamp)
                    data = data[data['date'] >= start_time]
                    if found_order.direction == Direction.LONG:
                        price = data['close'].min()
                        if price < found_order.price:
                            target_hit = 1
                    else:
                        price = data['close'].max()
                        if price > found_order.price:
                            target_hit = 1
                    if target_hit == 1:
                        found_order.quantity = order_book[b_order].quantity
                        found_order.filled_quantity = order_book[b_order].quantity
                        found_order.pending_quantity = 0
                        found_order.order_status = OrderStatus.COMPLETE
                    
                        found_order.price = order_book[b_order].price
                        found_order.trigger_price = order_book[b_order].trigger_price
                        found_order.average_price = order_book[b_order].price
                        logging.info('%s Updated order %s', self.broker, found_order)
                    else:
                        found_order.quantity = order_book[b_order].quantity
                        found_order.filled_quantity = 0
                        found_order.pending_quantity = order_book[b_order].quantity
                        found_order.order_status = OrderStatus.OPEN
                    
                        found_order.price = order_book[b_order].price
                        found_order.trigger_price = order_book[b_order].trigger_price
                        found_order.average_price = 0
                        logging.info('%s Updated order %s', self.broker, found_order)

                    num_orders_updated += 1
                
                else:
                    found_order.quantity = order_book[b_order].quantity
                    found_order.filled_quantity = order_book[b_order].quantity
                    found_order.pending_quantity = 0
                    found_order.order_status = OrderStatus.COMPLETE
                
                    found_order.price = order_book[b_order].price
                    found_order.trigger_price = order_book[b_order].trigger_price
                    found_order.average_price = order_book[b_order].price
                    logging.info('%s Updated order %s', self.broker, found_order)

                    num_orders_updated += 1

        logging.info('%s: %d orders updated with broker order details', self.broker, num_orders_updated)