import logging
import datetime
import time
import uuid
from collections import defaultdict
from Models.direction import Direction
from Models.producttype import ZerodhaProductType, FyersProductType
from Strategies.niftyshortstraddle import NiftyShortStraddle
from Strategies.basestrategy import BaseStrategy
from Utils.utils import get_epoch, round_to_nse_price, get_time_of_today
from Trademanagement.trademanager import TradeManager
from Trademanagement.trade import Trade
from Trademanagement.tradestate import TradeState

class NiftyShortStraddleISL920rentry1330(BaseStrategy):
    __instance = None

    @staticmethod
    def get_instance():
        if NiftyShortStraddleISL920rentry1330.__instance is None:
            return NiftyShortStraddleISL920rentry1330()
        return NiftyShortStraddleISL920rentry1330.__instance
    
    def __init__(self):
        if NiftyShortStraddleISL920rentry1330.__instance:
            raise Exception('This class is a singleton!')
        else:
            NiftyShortStraddleISL920rentry1330.__instance = self
        super().__init__('NiftyShortStraddleISL920rentry1330')

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
        hour, minute, second = list(map(int, cfg[name]['reentry_time'].split(':')))#datetime.datetime.strptime(, '%H:%M:%S')
        self.reentry_time = get_time_of_today(hour, minute, second)
        self.straddle = defaultdict(list)
    
    def process(self):
        now = datetime.datetime.now()
        if now < self.start_timestamp:
            return
        if self.num_trades >= self.max_trades_per_day:
            return
        if self.num_trades < 1:
            straddle = NiftyShortStraddle.get_straddle_combination()
            ce_symbol = straddle['ce']['trading_symbol']
            pe_symbol = straddle['pe']['trading_symbol']
            logging.info('%s: ATMCESymbol: %s, ATMPESymbol: %s', self.get_name(), ce_symbol, pe_symbol)
            for user in TradeManager.users:
                print(user.uid)
                if self.get_name() in user.subscribed_strategies:
                    print('Generating trades')
                    self.generate_trades(straddle, user)
            self.num_trades += 1
        elif self.num_trades < self.max_trades_per_day and now < self.reentry_time:
            for trade in self.trades:
                if trade.tradestate != TradeState.COMPLETED:
                    return
            straddle = NiftyShortStraddle.get_straddle_combination()
            ce_symbol = straddle['ce']['trading_symbol']
            pe_symbol = straddle['pe']['trading_symbol']
            logging.info('%s: ATMCESymbol: %s, ATMPESymbol: %s', self.get_name(), ce_symbol, pe_symbol)
            
            for user in TradeManager.users:
                if self.get_name() in user.subscribed_strategies:
                    self.generate_trades(straddle, user)
            self.num_trades += 1
            

    
    def generate_trades(self, straddle, user):
        # num_lots = self.calculate_lots_per_trade()
        ce_symbol = straddle['ce']['trading_symbol']
        pe_symbol = straddle['pe']['trading_symbol']
        straddle_combo_price = NiftyShortStraddle.get_straddle_combo_price(ce_symbol, pe_symbol)
        if not straddle_combo_price:
            logging.error('%s: Could not get straddle combo price for symbols %s, %s', self.get_name(), ce_symbol, pe_symbol)
            return
        ce_price = straddle_combo_price[0]
        pe_price = straddle_combo_price[1]
        straddle_id = str(uuid.uuid4())
        self.generate_trade(straddle['ce'], ce_price, 'CE', straddle_id, user)
        self.generate_trade(straddle['pe'], pe_price, 'PE', straddle_id, user)
        logging.info('%s: Trades generated.', self.get_name())
        
        
    
    def generate_trade(self, symbol_dict, ltp, option_type, straddle_id, user):

        symbol = symbol_dict['trading_symbol']
        ticker_symbol_dict = symbol_dict['symbol_dict']
        print(ticker_symbol_dict)
        uid = user.uid
        new_straddle_id = straddle_id + '-' + uid
        trade = Trade(symbol)
        trade.ticker_symbol_dict = ticker_symbol_dict
        trade.strategy = self.get_name()
        trade.broker = user.broker
        trade.uid = uid
        trade.is_options = True
        trade.direction = Direction.SHORT
        trade.product_type = self.product_type
        trade.place_market_order = False
        trade.requested_entry = ltp
        trade.timestamp = get_epoch(self.start_timestamp)

        lots, lot_size = self.get_quantity(user, trade)
        trade.quantity = int(lots * lot_size)
        trade.max_loss = -1 * lots * self.max_loss
        sl_amount = trade.requested_entry*self.call_sl_percent if option_type == "CE" else trade.requested_entry*self.put_sl_percent
        trade.stoploss = trade.requested_entry + sl_amount

        trade.intraday_square_off_timestamp = get_epoch(self.squareoff_timestamp)
        self.straddle[new_straddle_id].append(trade)
        trade.straddle_id = new_straddle_id
        TradeManager.add_new_trade(trade)
    
    def should_place_trade(self, trade, tick):
        if not super().should_place_trade(trade, tick):
            return False
        return True