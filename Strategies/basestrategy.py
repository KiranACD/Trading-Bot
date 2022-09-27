import logging
import time
import datetime
import configparser
from Instruments.instruments import Instruments

from Models.producttype import ZerodhaProductType, FyersProductType
from Models.quote import Quote
from Models.direction import Direction
from Trademanagement.trademanager import TradeManager
from Utils.utils import wait_till_market_opens, is_market_closed_for_day, get_market_start_time, get_epoch, get_time_of_today

class BaseStrategy:
    STRATEGY_CONFIG = None
    PRODUCT_TYPE = {'zerodha':{'MIS':ZerodhaProductType.MIS, 'CNC':ZerodhaProductType.CNC, 'NRML':ZerodhaProductType.NRML}}
    def __init__(self, name):
        self.name = name
        self.get_strategy_config()
        self.symbols = []     
        TradeManager.register_strategy(self)
        self.trades = TradeManager.get_all_trades_by_strategy(self.name)
    
    def get_strategy_config(self):
        if not BaseStrategy.STRATEGY_CONFIG:
            cfg = configparser.ConfigParser()
            cfg.read('ConfigFiles/strategy_config.ini')
            BaseStrategy.STRATEGY_CONFIG = cfg
        else:
            cfg = BaseStrategy.STRATEGY_CONFIG
        name = self.get_name()
        self.enabled = cfg[name]['enabled']
        self.product_type = cfg[name]['product_type'] # intraday / positional
        try:
            self.symbols_to_subscribe = cfg[name]['symbols_to_subscribe'].replace(' ', '').split(',')
            self.symbols_to_subscribe = [symbol for symbol in self.symbols_to_subscribe if symbol]
        except:
            self.symbols_to_subscribe = []
        hour, minute, second = list(map(int, cfg[name]['start_time'].split(':')))#datetime.datetime.strptime(, '%H:%M:%S')
        self.start_timestamp = get_time_of_today(hour, minute, second)
        hour, minute, second = list(map(int, cfg[name]['stop_time'].split(':')))#datetime.datetime.strptime(cfg[name]['stop_time'], '%H:%M:%S')
        self.stop_timestamp = get_time_of_today(hour, minute, second)
        print(self.start_timestamp)
        print(self.stop_timestamp)
        hour, minute, second = list(map(int, cfg[name]['squareoff_time'].split(':')))
        self.squareoff_timestamp = get_time_of_today(hour, minute, second)#datetime.datetime.strptime(cfg[name]['squareoff_time'], '%H:%M:%S')
        # self.capital = cfg[name]['capital'] # Capital allocated to each uid
        self.capital_per_set = float(cfg[name]['capital_per_set'])
        self.leverage = int(cfg[name]['leverage'])
        self.max_trades_per_day = int(cfg[name]['max_trades_per_day'])
        self.num_trades = 0
        self.is_fno = bool(cfg[name]['is_fno'])
        self.move_sl_to_cost = bool(int(cfg[name]['move_sl_to_cost']))
        return cfg

    def get_name(self):
        return self.name
    
    def is_enabled(self):
        return self.enabled
    
    def set_disabled(self):
        self.enabled = False
    
    def process(self):
        logging.info('BaseStrategy process is called.')
        pass
    
    def calculate_capital_per_trade(self):
        leverage = self.leverage if self.leverage > 0 else 1
        capital_per_trade = int(self.capital * leverage / self.max_trades_per_day)
        return capital_per_trade
    
    def calculate_lots_per_trade(self, user, trade):
        if trade.direction == Direction.LONG:
            capital = user.strategy_capital_map[trade.strategy]*user.capital*self.leverage
            lot_size = Instruments.get_lot_size(trade.trading_symbol, user.uid)
            lots = capital//lot_size
        else:
            lots = user.strategy_capital_map[trade.strategy]
            # lots = capital//self.capital_per_set
            lot_size = Instruments.get_lot_size(trade.trading_symbol, user.uid)
        return lots, lot_size
        
    def get_quantity(self, user, trade):
        print('is_fno base: ', self.is_fno)
        if self.is_fno:
            return self.calculate_lots_per_trade(user, trade)
        else:
            return 0, 0

    def can_trade_today(self):
        '''
        Derived class should override the logic if strategy to be traded only on specific days...
        ...of the week
        '''
        return True
    
    def run(self):
        '''
        This function should not be overridden in the derived class
        '''
        logging.info(f'{self.get_name()}: Strategy starting.')
        if not self.enabled:
            logging.warn('%s: Not going to run strategy as it is not enabled', self.get_name())
            return
        
        if is_market_closed_for_day():
            logging.warn('%s: Not going to run strategy as market is closed.', self.get_name())
            return

        now = datetime.datetime.now()
        if now < get_market_start_time():
            wait_till_market_opens(self.get_name())
        
        if not self.can_trade_today():
            logging.warn('%s: Not going to run strategy as it cannot be traded today.', self.get_name())
            return
        
        now = datetime.datetime.now()
        if now < self.start_timestamp:
            wait_seconds = get_epoch(self.start_timestamp) - get_epoch(now)
            logging.info('%s: Waiting for %d seconds till strategy start timestamp reaches...', self.get_name(), wait_seconds)
            if wait_seconds > 0:
                time.sleep(wait_seconds)
        
        while True:
            if is_market_closed_for_day():
                self.update_before_close()
                logging.warn('%s: Exiting the strategy as market closed.', self.get_name())
                break

            self.process()

            # now = datetime.datetime.now()
            # wait_seconds = 30-(now.second%30)
            # time.sleep(wait_seconds)
            time.sleep(5)
    
    def should_place_trade(self, trade, tick):
        '''
        Each strategy should call this function from its own should_place_trade() method before...
        ...working on its own logic
        '''
        if trade is None:
            return False
        if trade.quantity == 0:
            TradeManager.disable_trade(trade, 'InvalidQuantity')
            return False
        now = datetime.datetime.now()
        if now > self.stop_timestamp:
            TradeManager.disable_trade(trade, 'NoNewTradesCutOffTimeReached')
            return False
        num_of_trades_placed = TradeManager.get_number_of_trades_placed_by_strategy(self.get_name())
        if num_of_trades_placed >= self.max_trades_per_day:
            TradeManager.disable_trade(trade, 'MaxTradesPerDayReached')
            return False
        return True
    
    def add_trade_to_list(self, trade):
        if trade:
            self.trades.append(trade)
    
    def should_move_sl_to_cost(self):
        return self.move_sl_to_cost
    
    def get_trailing_sl(self, trade):
        return 0
    
    def update_before_close(self):
        return
    
    def should_place_sl(self, trade):
        return
    
    def should_place_target(self, trade):
        return
    
    def should_partial_exit(self, trade):
        return
    
    def update_flags(self, trade, context=None):
        return
    