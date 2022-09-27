import logging
import datetime

from collections import defaultdict, deque
from Instruments.instruments import Instruments
from Models.direction import Direction
from Models.producttype import ZerodhaProductType, FyersProductType
from Quotes.quotes import Quotes
from Strategies.bankniftyshortstraddle import BankniftyShortStraddle
from Strategies.basestrategy import BaseStrategy
from Utils.utils import get_epoch, round_to_nse_price, get_expiry
from Config.config import get_server_config
from Trademanagement.trademanager import TradeManager
from Trademanagement.trade import Trade
from BrokerController.brokercontroller import BrokerController

class BankniftyStraddleAdjust(BaseStrategy):
    __instance = None

    @staticmethod
    def get_instance():
        if BankniftyStraddleAdjust.__instance is None:
            return BankniftyStraddleAdjust()
        return BankniftyStraddleAdjust.__instance
    
    def __init__(self):
        if BankniftyStraddleAdjust.__instance:
            raise Exception('This class is a singleton!')
        else:
            BankniftyStraddleAdjust.__instance = self
        super().__init__('BankniftyStraddleAdjust')

    def get_strategy_config(self):
        cfg = super().get_strategy_config()
        name = self.get_name()
        self.underlying = cfg[name]['underlying']
        self.base = cfg[name]['base']
        self.expiry = cfg[name]['expiry']
        self.max_loss = float(cfg[name]['max_loss'])
        self.days_to_trade = cfg[name]['days_to_trade'].replace(' ', '').split(',')
        self.delta = float(cfg[name]['delta'])
        self.ce_list = defaultdict(deque)
        self.pe_list = defaultdict(deque)
        self.underlying_price = None
        while True:
            expiry = get_expiry(self.underlying, 'current', 'FUT')
            if expiry:
                logging.info(f'{self.get_name()}: Fetched futures expiry.')
                break
            logging.info(f'{self.get_name()}: Not fetched futures expiry.')
        symbol = {'name':self.underlying, 'instrument_type':'FUT', 'strike':0, 'expiry':expiry, 'exchange':'NFO'}
        historical_data_broker = get_server_config()['historical_broker']
        self.data_uid = BrokerController.get_historical_broker_uid(historical_data_broker)
        self.underlying_trading_symbol = Instruments.get_trading_symbol(symbol, self.data_uid)
        self.last_checked_timestamp = None
        self.new_ce_straddle = 0
        self.new_pe_straddle = 0
    
    def process(self):
        now = datetime.datetime.now()
        if now<self.start_timestamp:
            logging.info(f'{self.get_name()}: Not yet at start time.')
            return
        if self.num_trades >= self.max_trades_per_day:
            logging.info(f'{self.get_name()}: Max trades hit for the day.')
            return
        
        if not self.underlying_price:
            logging.info(f'{self.get_name()}: Underlying price is not set.')
            if not TradeManager.users:
                logging.info(f'{self.get_name()}: Users not logged in yet.')
                return
            self.underlying_price = Quotes.get_fno_quote(self.underlying_trading_symbol, self.data_uid).last_traded_price
            self.last_checked_timestamp = get_epoch()
            straddle = BankniftyShortStraddle.get_straddle_combination()
            ce_symbol = straddle['ce']['trading_symbol']
            pe_symbol = straddle['pe']['trading_symbol']
            # self.ce_list.append(ce_symbol)
            # self.pe_list.append(pe_symbol)
            logging.info('%s: ATMCESymbol: %s, ATMPESymbol: %s', self.get_name(), ce_symbol, pe_symbol)
            for user in TradeManager.users:
                if self.get_name() in user.subscribed_strategies:
                    uid = user.uid
                    self.generate_trades(straddle, user)
            self.num_trades += 1
        
        now_epoch = get_epoch()
        if (now_epoch - self.last_checked_timestamp) >= 300:
            # logging.info(f'{self.get_name()}: CE trades: {self.ce_list}, PE trades: {self.pe_list}')
            self.last_checked_timestamp = now_epoch
            now_epoch = get_epoch()
            underlying_ltp = Quotes.get_fno_quote(self.underlying_trading_symbol, self.data_uid).last_traded_price
            if (underlying_ltp - self.underlying_price) >= self.delta:
                logging.info(f'{self.get_name()}: Satisfied updelta. Cuurent trade => CE trades: {self.ce_list}, PE trades: {self.pe_list}')
                self.underlying_price = underlying_ltp
                for user in TradeManager.users:
                    if self.get_name() in user.subscribed_strategies:
                        uid = user.uid
                        self.exit_ce_sl(uid)
                        if len(self.pe_list[uid]) == 2:
                            self.exit_pe_target(uid)
                        straddle = BankniftyShortStraddle.get_straddle_combination()
                        if straddle is None:
                            continue
                        ce_symbol = straddle['ce']['trading_symbol']
                        pe_symbol = straddle['pe']['trading_symbol']
                        straddle_combo_price = BankniftyShortStraddle.get_straddle_combo_price(ce_symbol, pe_symbol)
                        if straddle_combo_price is None:
                            continue
                        if self.ce_list[uid]:
                            ltp = straddle_combo_price[1]
                            logging.info('%s: ATMPESymbol: %s', self.get_name(), pe_symbol)
                            self.generate_trade(straddle['pe'], ltp, 'PE', user)
                        else:
                            logging.info('%s: ATMCESymbol: %s, ATMPESymbol: %s', self.get_name(), ce_symbol, pe_symbol)
                            self.generate_trades(straddle, user)
                self.num_trades += 1
                
            elif (underlying_ltp - self.underlying_price) <= (-1*self.delta):
                logging.info(f'{self.get_name()}: Satisfied downdelta. Cuurent trade => CE trades: {self.ce_list}, PE trades: {self.pe_list}')
                self.underlying_price = underlying_ltp
                for user in TradeManager.users:
                    if self.get_name() in user.subscribed_strategies:
                        uid = user.uid
                        self.exit_pe_sl(uid)
                        if len(self.ce_list[uid]) == 2:
                            self.exit_ce_target(uid)
                        straddle = BankniftyShortStraddle.get_straddle_combination()
                        if straddle is None:
                            continue
                        ce_symbol = straddle['ce']['trading_symbol']
                        pe_symbol = straddle['pe']['trading_symbol']
                        straddle_combo_price = BankniftyShortStraddle.get_straddle_combo_price(ce_symbol, pe_symbol)
                        if straddle_combo_price is None:
                            continue
                        if self.pe_list[uid]:
                            ltp = straddle_combo_price[0]
                            logging.info('%s: ATMCESymbol: %s', self.get_name(), ce_symbol)
                            self.generate_trade(straddle['ce'], ltp, 'CE', user)
                        else:
                            logging.info('%s: ATMCESymbol: %s, ATMPESymbol: %s', self.get_name(), ce_symbol, pe_symbol)
                            self.generate_trades(straddle, user)
                self.num_trades += 1
    
    def generate_trades(self, straddle, user):
        ce_symbol = straddle['ce']['trading_symbol']
        pe_symbol = straddle['pe']['trading_symbol']
        straddle_combo_price = BankniftyShortStraddle.get_straddle_combo_price(ce_symbol, pe_symbol)
        if not straddle_combo_price:
            logging.error('%s: Could not generate trades', self.get_name())
            return
        ce_price = straddle_combo_price[0]
        pe_price = straddle_combo_price[1]
        self.generate_trade(straddle['ce'], ce_price, 'CE', user)
        self.generate_trade(straddle['pe'], pe_price, 'PE', user)
        logging.info('%s: Trades generated.', self.get_name())
    
    def generate_trade(self, symbol_dict, ltp, option_type, user):
        symbol = symbol_dict['trading_symbol']
        ticker_symbol_dict = symbol_dict['symbol_dict']
        uid = user.uid
        trade = Trade(symbol)
        trade.ticker_symbol_dict = ticker_symbol_dict
        trade.underlying = self.underlying
        trade.underlying_price = self.underlying_price
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

        trade.intraday_squareoff_timestamp = get_epoch(self.squareoff_timestamp)
        TradeManager.add_new_trade(trade)
        if option_type == 'CE':
            self.ce_list[uid].append(trade)
        else:
            self.pe_list[uid].append(trade)
    
    def exit_ce_sl(self, uid):
        trade = self.ce_list[uid].pop()
        try:
            ltp = Quotes.get_fno_quote(trade.trading_symbol, self.data_uid).last_traded_price
        except Exception as e:
            logging.error(f'Could not get {trade.trading_symbol} quote. Could not place sl.')
            return
        trade.stoploss = ltp
    
    def exit_pe_target(self, uid):
        trade = self.pe_list[uid].popleft()
        try:
            ltp = Quotes.get_fno_quote(trade.trading_symbol, self.data_uid).last_traded_price
        except Exception as e:
            logging.error(f'Could not get {trade.trading_symbol} quote. Could not place sl.')
            return
        trade.target = ltp
    
    def exit_pe_sl(self, uid):
        trade = self.pe_list[uid].pop()
        try:
            ltp = Quotes.get_fno_quote(trade.trading_symbol, self.data_uid).last_traded_price
        except Exception as e:
            logging.error(f'Could not get {trade.trading_symbol} quote. Could not place sl.')
            return
        trade.stoploss = ltp
    
    def exit_ce_target(self, uid):
        trade = self.ce_list[uid].popleft()
        try:
            ltp = Quotes.get_fno_quote(trade.trading_symbol, self.data_uid).last_traded_price
        except Exception as e:
            logging.error(f'Could not get {trade.trading_symbol} quote. Could not place sl.')
            return
        trade.target = ltp


    def should_place_trade(self, trade, tick):
        if not super().should_place_trade(trade, tick):
            return False
        if trade.option_type == 'CE' and len(self.ce_list[trade.uid]) >= 2:
            return False
        if trade.option_type == 'PE' and len(self.pe_list[trade.uid]) >= 2:
            return False
        return True


