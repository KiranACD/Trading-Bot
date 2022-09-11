import logging
import datetime
import pandas as pd

from Instruments.instruments import Instruments
from Models.direction import Direction
from Models.producttype import ZerodhaProductType, FyersProductType
from Strategies.basestrategy import BaseStrategy
from Utils.utils import get_epoch, round_to_nse_price
from Trademanagement.trademanager import TradeManager
from Trademanagement.trade import Trade

class FractalStrategy(BaseStrategy):
    __instance = None

    @staticmethod
    def get_instance():
        if FractalStrategy.__instance is None:
            return FractalStrategy()
        return FractalStrategy.__instance
    
    def __init__(self):
        if FractalStrategy.__instance:
            raise Exception('This class is a singleton!')
        else:
            FractalStrategy.__instance = self

        super().__init__('FractalStrategy')
    
    def get_strategy_config(self):
        cfg = super().get_strategy_config()
        name = self.get_name()
        self.underlying = cfg[name]['underlying']
        self.base = cfg[name]['base']
        self.expiry = cfg[name]['expiry']
        self.sl_percent = cfg[name]['sl_percent']
        self.target = cfg[name]['target_percent']
        self.quantity_mutiplier = cfg[name]['quantity_multiplier']
        self.days_to_trade = cfg[name]['days_to_trade'].replace(' ', '').split(',')
        self.timeframe = cfg[name]['timeframe']
        self.fractal_lookback = cfg[name]['fractal_looback']
        self.supertrend_lookback = cfg[name]['supertrend_lookback']
        self.supertrend_multiplier = cfg[name]['supertrend_multiplier']
        self.underlying_history_filename = cfg[name]['underlying_history_filename']

        self.underlying_history = pd.read_pickle(self.underlying_history_filename)
        self.signal_high = None
        self.signal_low = None
        self.long_trade = 0
        self.short_trade = 0
    
    def process(self):
        now = datetime.datetime.now()
        if now < self.start_timestamp:
            return
        if self.num_trades >= self.max_trades_per_day:
            return
        
    def update_historical_data(self):
        # Get the historical data from zerodha and update self.underlying_history.
        # Update the indicators. 
        
        pass
        

