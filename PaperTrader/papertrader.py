import random
import logging
from Models.orderstatus import OrderStatus
from Models.ordertype import OrderType
from Ordermanagement.order import Order
from Models.direction import Direction
from Utils.utils import get_epoch

class PaperTrader:
    orderbook = []
    tradebook = []

    @staticmethod
    def place_order(orderinputparams):
        order_id = random.randint(1000, 10000)
        order = Order(orderinputparams)
        order.order_id = order_id
        order.orderplacetimestamp = get_epoch()
        order.lastorderupdatetimestamp = get_epoch()
        order.order_status = OrderStatus.OPEN
        PaperTrader.add_to_orderbook(order)
        logging.info('%s: Order added to orderbook, orderId = %s', 'PaperTrader', order_id)
        return order_id

    @staticmethod
    def modify_order(order, omp):
        foundorder = None
        orderbook = PaperTrader.get_orderbook()
        for border in orderbook:
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
        return None

    @staticmethod
    def cancel_order(order):
        foundorder = None
        orderbook = PaperTrader.get_orderbook()
        for border in orderbook:
            if order.order_id == border.order_id:
                foundorder = border
                break
        if foundorder and foundorder.order_status == OrderStatus.OPEN:
            foundorder.order_status = OrderStatus.CANCELLED
            PaperTrader.add_to_tradebook(foundorder)
            return foundorder.order_id
        return None

    @staticmethod
    def add_to_tradebook(order):
        PaperTrader.tradebook.append(order)

    @staticmethod
    def update_orders(tick):
        foundorders = []
        orderbook = PaperTrader.get_orderbook()
        for border in orderbook:
            if tick.trading_symbol == border.trading_symbol and border.order_status == OrderStatus.OPEN:
                foundorders.append(border)
        
        for order in foundorders:
            if order.order_ == 'entry_order':
                order.average_price = tick.last_traded_price
                order.filled_quantity = order.quantity
                order.order_status = OrderStatus.COMPLETE
                PaperTrader.add_to_tradebook(order)
            elif order.order_ == 'sl_order':
                if order.direction == Direction.LONG:
                    if order.order_type == OrderType.SL_MARKET:
                        if tick.last_traded_price >= order.trigger_price:
                            order.average_price = tick.last_traded_price
                            order.filled_quantity = order.quantity
                            order.order_status = OrderStatus.COMPLETE
                            PaperTrader.add_to_tradebook(order)
                    elif order.order_type == OrderType.MARKET:
                        order.average_price = tick.last_traded_price
                        order.filled_quantity = order.quantity
                        order.order_status = OrderStatus.COMPLETE
                        PaperTrader.add_to_tradebook(order)
                else:
                    if order.order_type == OrderType.SL_MARKET:
                        if tick.last_traded_price <= order.trigger_price:
                            order.average_price = tick.last_traded_price
                            order.filled_quantity = order.quantity
                            order.order_status = OrderStatus.COMPLETE
                            PaperTrader.add_to_tradebook(order)
                    elif order.order_type == OrderType.MARKET:
                        order.average_price = tick.last_traded_price
                        order.filled_quantity = order.quantity
                        order.order_status = OrderStatus.COMPLETE
                        PaperTrader.add_to_tradebook(order)
            elif order.order_ == 'target_order':
                if order.direction == Direction.LONG:
                    if order.order_type == OrderType.LIMIT:
                        if tick.last_traded_price <= order.trigger_price:
                            order.average_price = tick.last_traded_price
                            order.filled_quantity = order.quantity
                            order.order_status = OrderStatus.COMPLETE
                            PaperTrader.add_to_tradebook(order)
                    elif order.order_type == OrderType.MARKET:
                        order.average_price = tick.last_traded_price
                        order.filled_quantity = order.quantiy
                        order.order_status = OrderStatus.COMPLETE
                        PaperTrader.add_to_tradebook(order)
                else:
                    if order.order_type == OrderType.LIMIT:
                        if tick.last_traded_price >= order.trigger_price:
                            order.average_price = tick.last_traded_price
                            order.filled_quantity = order.quantity
                            order.order_status = OrderStatus.COMPLETE
                            PaperTrader.add_to_tradebook(order)
                    elif order.order_type == OrderType.MARKET:
                        order.average_price = tick.last_traded_price
                        order.filled_quantity = order.quantiy
                        order.order_status = OrderStatus.COMPLETE
                        PaperTrader.add_to_tradebook(order)


    @staticmethod
    def get_orderbook():
        return PaperTrader.orderbook
    
    @staticmethod
    def add_to_orderbook(order):
        PaperTrader.orderbook.append(order)
    
    @staticmethod
    def get_tradebook():
        return PaperTrader.tradebook
