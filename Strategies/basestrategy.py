import logging
import time
import datetime
import configparser

from Models.producttype import ZerodhaProductType, FyersProductType
from Models.quote import Quote
from Trademanagement.trademanager import TradeManager
from Utils.utils import wait_till_market_opens, is_market_closed_for_day, get_market_start_time, get_epoch

class BaseStrategy:
    STRATEGY_CONFIG = None
    PRODUCT_TYPE = {'zerodha':{'MIS':ZerodhaProductType.MIS, 'CNC':ZerodhaProductType.CNC, 'NRML':ZerodhaProductType.NRML}}
    def __init__(self, name):
        self.name = name
        self.get_strategy_config()

        self.symbols = []
        self.is_fno = False
        self.capital_per_set = 0
        
        TradeManager.register_strategy(self)
        self.trades = TradeManager.get_all_trades_by_strategy(self.name)
    
    def get_strategy_config(self):
        if not BaseStrategy.STRATEGY_CONFIG:
            cfg = configparser.ConfigParser()
            cfg.read('ConfigFiles/strategy.ini')
            BaseStrategy.STRATEGY_CONFIG = cfg
        else:
            cfg = BaseStrategy.STRATEGY_CONFIG   

        name = self.get_name()
        self.enabled = cfg[name]['enabled']
        self.uids = cfg[name]['uids'].replace(' ','').split(',')
        self.product_type = cfg[name]['product_type'] # intraday / positional
        try:
            self.symbols_to_subscribe = cfg[name]['symbols_to_subscribe'].replace(' ', '').split(',')
        except:
            self.symbols_to_subscribe = []
        self.data_uid = cfg[name]['data_uid']
        self.start_timestamp = datetime.datetime.strptime(cfg[name]['start_timestamp'], '%H:%M:%S') 
        self.stop_timestamp = datetime.datetime.strptime(cfg[name]['stop_timestamp'], '%H:%M:%S')
        self.squareoff_timestamp = datetime.datetime.strptime(cfg[name]['squaroff_timestamp'], '%H:%M:%S')
        self.capital = cfg[name]['capital'].replace(' ', '').split(',') # Capital allocated to each uid
        self.capital_per_set = cfg[name]['capital_per_set']
        self.leverage = cfg[name]['leverage']
        self.max_trades_per_day = cfg[name]['max_trades_per_day']
        self.num_trades = 0
        self.is_fno = cfg[name]['is_fno']
        
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
    
    def calculate_lots_per_trade(self):
        if not self.is_fno:
            return 0
        return [cap//self.capital_per_set for cap in self.capital]
        
    
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
        if not self.enabled:
            logging.warn('%s: Not going to run strategy as it is not enabled', self.get_name())
            return
        
        if is_market_closed_for_day():
            logging.warn('%s: Not going to run strategy as market is closed.', self.get_name())
            return
        
        self.process()

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
                logging.warn('%s: Exiting the strategy as market closed.', self.get_name())
                break

            self.process()

            now = datetime.datetime.now()
            wait_seconds = 30-(now.second%30)
            time.sleep(wait_seconds)
    
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
    