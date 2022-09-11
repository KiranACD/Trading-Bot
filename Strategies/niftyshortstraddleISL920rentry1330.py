import logging
import datetime
import uuid
import configparser
from collections import defaultdict
from Instruments.instruments import Instruments
from Models.direction import Direction
from Models.producttype import ZerodhaProductType, FyersProductType
from Strategies.niftyshortstraddle import NiftyShortStraddle
from Strategies.basestrategy import BaseStrategy
from Utils.utils import get_epoch, round_to_nse_price
from Trademanagement.trademanager import TradeManager
from Trademanagement.trade import Trade
from Trademanagement.tradestate import TradeState

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
        self.max_loss = cfg[name]['max_loss']
        self.call_target_percent = cfg[name]['call_target_percent']
        self.put_target_percent = cfg[name]['put_target_percent']
        self.days_to_trade = cfg[name]['days_to_trade'].replace(' ', '').split(',')
        self.rentry_time = datetime.datetime.strptime(cfg[name]['rentry_time'], '%H:%M:%S')
        self.straddle = defaultdict(list)
    
    def process(self):
        now = datetime.datetime.now()
        if now < self.start_timestamp:
            return
        if self.num_trades >= self.max_trades_per_day:
            return
        if self.num_trades < 1:
            ce_symbol, pe_symbol = NiftyShortStraddle.get_straddle_combination()
            logging.info('%s: ATMCESymbol: %s, ATMPESymbol: %s', self.get_name(), ce_symbol, pe_symbol)
            self.generate_trades(ce_symbol, pe_symbol)
        elif self.num_trades < self.max_trades_per_day and now < self.rentry_time:
            for trade in self.trades:
                if trade.tradestatus != TradeState.COMPLETED:
                    return
            ce_symbol, pe_symbol = NiftyShortStraddle.get_straddle_combination()
            logging.info('%s: ATMCESymbol: %s, ATMPESymbol: %s', self.get_name(), ce_symbol, pe_symbol)
            self.generate_trades(ce_symbol, pe_symbol)
            

    
    def generate_trades(self, ce_symbol, pe_symbol):
        # num_lots = self.calculate_lots_per_trade()
        straddle_combo_price = NiftyShortStraddle.get_straddle_combo_price(ce_symbol, pe_symbol)
        if not straddle_combo_price:
            logging.error('%s: Could not get straddle combo price for symbols %s, %s', self.get_name(), ce_symbol, pe_symbol)
            return
        ce_price = straddle_combo_price[0]
        pe_price = straddle_combo_price[1]
        straddle_id = str(uuid.uuid4())
        self.generate_trade(ce_symbol, ce_price, 'CE', straddle_id)
        self.generate_trade(pe_symbol, pe_price, 'PE', straddle_id)
        logging.info('%s: Trades generated.', self.get_name())
        self.num_trades += 1
    
    def generate_trade(self, symbol, ltp, option_type, straddle_id):

        for user in TradeManager.users:
            if self.get_name() in user.subscribed_strategies:
                uid = user.uid
                new_straddle_id = straddle_id + '-' + uid
                trade = Trade(symbol)
                trade.strategy = self.get_name()
                trade.uid = uid
                trade.is_options = True
                trade.direction = Direction.SHORT
                trade.product_type = self.product_type
                trade.place_market_order = False
                trade.requested_entry = ltp
                trade.timestamp = get_epoch(self.start_timestamp)

                trade.quantity = self.get_quantity(user, trade)

                sl_amount = trade.requested_entry*self.call_sl_percent if option_type == "CE" else trade.requested_entry*self.put_sl_percent
                trade.stoploss = trade.requested_entry + sl_amount
                target_amount = trade.requested_entry*self.call_target_percent if option_type == "CE" else trade.requested_entry*self.put_target_percent
                trade.target = trade.requested_entry - target_amount

                trade.intraday_square_off_timestamp = get_epoch(self.squareoff_timestamp)
                self.straddle[new_straddle_id].append(trade)
                trade.straddle_id = new_straddle_id
                TradeManager.add_new_trade(trade)
    
    def should_place_trade(self, trade, tick):
        if not super().should_place_trade(trade, tick):
            return False
        return True