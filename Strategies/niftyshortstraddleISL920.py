import logging
import datetime
import configparser

from Instruments.instruments import Instruments
from Models.direction import Direction
from Models.producttype import ZerodhaProductType, FyersProductType
from Strategies.niftyshortstraddle import NiftyShortStraddle
from Strategies.basestrategy import BaseStrategy
from Utils.utils import get_epoch, round_to_nse_price
from Trademanagement.trademanager import TradeManager
from Trademanagement.trade import Trade

class NiftyShortStraddleISL920(BaseStrategy):
    __instance = None

    @staticmethod
    def get_instance():
        if NiftyShortStraddleISL920.__instance is None:
            return NiftyShortStraddleISL920()
        return NiftyShortStraddleISL920.__instance
    
    def __init__(self):
        if NiftyShortStraddleISL920.__instance:
            raise Exception('This class is a singleton!')
        else:
            NiftyShortStraddleISL920.__instance = self
        super().__init__('ShortStraddleISL920')

    def get_strategy_config(self):
        cfg = super().get_strategy_config()
        name = self.get_name()
        self.underlying = cfg[name]['underlying']
        self.number_of_strikes = cfg[name]['number_of_strikes']
        self.base = cfg[name]['base']
        self.expiry = cfg[name]['expiry']
        self.call_sl_percent = cfg[name]['call_sl_percent']
        self.put_sl_percent = cfg[name]['put_sl_percent']
        self.call_target_percent = cfg[name]['call_target_percent']
        self.put_target_percent = cfg[name]['put_target_percent']
        self.days_to_trade = cfg[name]['days_to_trade'].replace(' ', '').split(',')
    
    def process(self):
        now = datetime.datetime.now()
        if now < self.start_timestamp:
            return
        if self.num_trades >= self.max_trades_per_day:
            return
        ce_symbol, pe_symbol = NiftyShortStraddle.get_straddle_combination()
        logging.info('%s: ATMCESymbol: %s, ATMPESymbol: %s', self.get_name(), ce_symbol, pe_symbol)
        self.generate_trades(ce_symbol, pe_symbol)
    
    def generate_trades(self, ce_symbol, pe_symbol):
        num_lots = self.calculate_lots_per_trade()
        uid = NiftyShortStraddle.config['uid']
        straddle_combo_price = NiftyShortStraddle.get_straddle_combo_price(ce_symbol, pe_symbol)
        if not straddle_combo_price:
            logging.error('%s: Could not generate trades', self.get_name())
            return
        ce_price = straddle_combo_price[0]
        pe_price = straddle_combo_price[1]
        
        self.generate_trade(ce_symbol, num_lots, ce_price, 'CE')
        self.generate_trade(pe_symbol, num_lots, pe_price, 'PE')
        logging.info('%s: Trades generated.', self.get_name())
    
    def generate_trade(self, symbol, num_lots, ltp, option_type):
        for lots, uid in zip(num_lots, self.uids):
            trade = Trade(symbol)
            trade.strategy = self.get_name()
            trade.is_options = True
            trade.direction = Direction.SHORT
            trade.product_type = self.product_type
            trade.place_market_order = False
            trade.requested_entry = ltp
            trade.timestamp = get_epoch(self.start_timestamp)

            lot_size = Instruments.get_lot_size(uid)
            trade.quantity = lot_size*num_lots

            sl_amount = trade.requested_entry*self.call_sl_percent if option_type == "CE" else trade.requested_entry*self.put_sl_percent
            trade.stoploss = trade.requested_entry + sl_amount
            target_amount = trade.requested_entry*self.call_target_percent if option_type == "CE" else trade.requested_entry*self.put_target_percent
            trade.target = trade.requested_entry - target_amount

            trade.intraday_square_off_timestamp = get_epoch(self.squareoff_timestamp)
            TradeManager.add_new_trade(trade)
    
    def should_place_trade(self, trade, tick):
        if not super().should_place_trade(trade, tick):
            return False
        return True




    


        