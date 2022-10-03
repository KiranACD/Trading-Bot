import logging
import datetime
import uuid
from collections import defaultdict
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
        super().__init__('NiftyShortStraddleISL920')

    def get_strategy_config(self):
        cfg = super().get_strategy_config()
        name = self.get_name()
        self.underlying = cfg[name]['underlying']
        self.base = float(cfg[name]['base'])
        self.expiry = cfg[name]['expiry']
        self.call_sl_percent = float(cfg[name]['call_sl_percent'])
        self.put_sl_percent = float(cfg[name]['put_sl_percent'])
        self.max_loss = float(cfg[name]['max_loss'])
        self.call_target_percent = float(cfg[name]['call_target_percent'])
        self.put_target_percent = float(cfg[name]['put_target_percent'])
        self.days_to_trade = cfg[name]['days_to_trade'].replace(' ', '').split(',')
        self.straddle = defaultdict(list)
    
    def process(self):
        now = datetime.datetime.now()
        if now < self.start_timestamp:
            return
        if self.num_trades >= self.max_trades_per_day:
            return
        straddle = NiftyShortStraddle.get_straddle_combination()
        ce_symbol = straddle['ce']['trading_symbol']
        pe_symbol = straddle['pe']['trading_symbol']
        logging.info('%s: ATMCESymbol: %s, ATMPESymbol: %s', self.get_name(), ce_symbol, pe_symbol)
        self.generate_trades(straddle)
    
    def generate_trades(self, straddle):
        # num_lots = self.calculate_lots_per_trade()
        ce_symbol = straddle['ce']['trading_symbol']
        pe_symbol = straddle['pe']['trading_symbol']
        straddle_combo_price = NiftyShortStraddle.get_straddle_combo_price(ce_symbol, pe_symbol)
        if not straddle_combo_price:
            logging.error('%s: Could not generate trades', self.get_name())
            return
        ce_price = straddle_combo_price[0]
        pe_price = straddle_combo_price[1]
        straddle_id = str(uuid.uuid4())
        self.generate_trade(straddle['ce'], ce_price, 'CE', straddle_id)
        self.generate_trade(straddle['pe'], pe_price, 'PE', straddle_id)
        logging.info('%s: Trades generated.', self.get_name())
    
    def generate_trade(self, symbol_dict, ltp, option_type, straddle_id):

        add_new_trade_flag = 0
        symbol = symbol_dict['trading_symbol']
        ticker_symbol_dict = symbol_dict['symbol_dict']
        for user in TradeManager.users:
            if self.get_name() in user.subscribed_strategies:
                uid = user.uid
                new_straddle_id = straddle_id + '-' + uid
                trade = Trade(symbol)
                trade.ticker_symbol_dict = ticker_symbol_dict
                trade.strategy = self.get_name()
                trade.uid = uid
                trade.broker = user.broker
                trade.exchange = ticker_symbol_dict['exchange']
                trade.is_options = True
                trade.direction = Direction.SHORT
                trade.product_type = self.product_type
                trade.place_market_order = False
                trade.requested_entry = ltp
                trade.timestamp = get_epoch(self.start_timestamp)
                
                lots, lot_size = self.get_quantity(user, trade)
                print('lots: ', lots, ' lot_size: ', lot_size)
                trade.quantity = int(lots * lot_size)
                trade.max_loss = -1 * lots * self.max_loss
                sl_amount = trade.requested_entry*self.call_sl_percent if option_type == "CE" else trade.requested_entry*self.put_sl_percent
                trade.stoploss = trade.requested_entry + sl_amount
                target_amount = trade.requested_entry*self.call_target_percent if option_type == "CE" else trade.requested_entry*self.put_target_percent
                trade.target = trade.requested_entry - target_amount

                trade.intraday_squareoff_timestamp = get_epoch(self.squareoff_timestamp)
                self.straddle[new_straddle_id].append(trade)
                trade.straddle_id = new_straddle_id
                if TradeManager.add_new_trade(trade):
                    add_new_trade_flag = 1
        if add_new_trade_flag:
            self.num_trades += 1
    
    def should_place_trade(self, trade, tick):
        if not super().should_place_trade(trade, tick):
            return False
        return True




    


        