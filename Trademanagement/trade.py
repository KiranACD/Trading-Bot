import logging
from Trademanagement.tradestate import TradeState
from Utils import utils

class Trade:
    def __init__(self, trading_symbol=None):
        self.exchange = ''
        self.trade_id = utils.generate_trade_id() # unique trade id.
        self.trading_symbol = trading_symbol
        self.broker = '' # name of broker in which strategy has to be executed
        self.uid = '' # user id to which orders have to be sent
        self.strategy = '' # name of strategy that generates the trade
        self.direction = '' # long or short
        self.product_type = '' # CNC/MIS. Depends onn broker
        self.is_futures = False # futures trade
        self.is_options = False # options trade
        self.straddle_id = None # straddle id. This will be the same for CE and PE leg of a straddle.
        self.option_type = None # CE/PE
        self.is_curency = False
        self.is_commodity = False
        self.place_market_order = False # when you place entry order with market order type
        self.intraday_square_off_timestamp = None # strategy specific squareoff time
        self.requested_entry = 0 # requested entry price
        self.entry = 0 # actual entry. This will be traded price at entry
        self.quantity = 0 # requested quantity
        self.filled_quantity = 0 # in case of partial fill, this will not be equal to quantity
        self.initial_stoploss = 0 # initial stoploss
        self.stoploss = 0 # current stoploss. In case of trailing stoploss, this will be different from initial stoploss.
        self.max_loss = 0 # max mtm loss
        self.target = 0 # target is applicable
        self.cmp = 0 # last traded price

        self.tradestate = TradeState.CREATED # state of the trade
        self.timestamp = None # set this timestamp to strategy timestamp if you are not sure what to set 
        self.create_timestamp = utils.get_epoch() # when trade is created, not triggered
        self.start_timestamp = None # when trade gets triggered and order placed
        self.end_timestamp = None # timestamp when trade ended
        self.pnl = 0 # Profit/loss of trade
        self.pnl_percentage = 0 # profit loss in percentage
        self.exit = 0 # Exit price of the trade
        self.exitreason = None # SL/Target/Squareoff/

        self.entry_order = None # object of type Order
        self.sl_order = None # object of type Order
        self.target_order = None # object of type Order
    
    def equals(self, trade):
        if trade is None:
            return False
        if self.trade_id == trade.trade_id:
            return True
        if self.trading_symbol != trade.trading_symbol:
            return False
        if self.strategy != trade.strategy:
            return False
        if self.direction != trade.direction:
            return False
        if self.product_type != trade.product_type:
            return False
        if self.requested_entry != trade.requested_entry:
            return False
        if self.quantity != trade.quantity:
            return False
        if self.timestamp != trade.timestamp:
            return False
        if self.uid != trade.uid:
            return False
        return True
    
    def __str__(self):
        return "ID = " + str(self.trade_id) + ", state = " + self.tradestate + ", symbol = " + \
               self.trading_symbol + ", strategy = " + self.strategy + ", direction = " + self.direction + \
               ", product_type = " + self.product_type + ", reqEntry = ", str(self.requested_entry) + \
                ", stoploss = " + str(self.stoploss) + ", target = " + str(self.target) \
               + ", entry = " + str(self.entry) + ", exit = " + str(self.exit) \
               + ", profitloss = " + str(self.pnl)
    