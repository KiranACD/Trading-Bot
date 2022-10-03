import logging
import datetime
from kiteconnect import KiteTicker
from Ticker.baseticker import BaseTicker
from BrokerController.brokercontroller import BrokerController
from Instruments.instruments import Instruments
from Models.tickdata import TickData
from Config import config
from Utils import filesystem, path

class ZerodhaTicker(BaseTicker):
    __instance = None
    broker_handle = None
    ticker = None
    listeners = []
    token_to_trading_symbol_map = {}

    @staticmethod
    def get_instance():
        if ZerodhaTicker.__instance is None:
            ZerodhaTicker()
        return ZerodhaTicker.__instance
    
    def __init__(self):
        if ZerodhaTicker.__instance is not None:
            raise Exception('This class is a singleton!')
        else:
            ZerodhaTicker.__instance = self
        super().__init__('ZerodhaTicker')

    def start_ticker(self):
        try:
            uid = BrokerController.get_ticker_broker_uid('zerodha')
        except Exception as e:
            logging.exception(f'Not logged in to Zerodha ticker account due to {e}')
            return
        
        uid_details = BrokerController.get_uid_details_uid(uid)
        access_token = uid_details['access_token']
        api_key = uid_details['api_key']

        ticker = KiteTicker(api_key, access_token)
        ticker.on_connect = self.on_connect
        ticker.on_close = self.on_close
        ticker.on_error = self.on_error
        ticker.on_reconnect = self.on_reconnect
        ticker.on_noreconnect = self.on_noreconnect
        ticker.on_ticks = self.on_ticks
        ticker.on_order_update = self.on_order_update

        logging.info('ZerodhaTicker: Going to connect...')
        self.ticker = ticker
        self.ticker.connect(threaded=True)
    
    def stop_ticker(self):
        logging.info('ZerodhaTicker: stopping...')
        self.ticker.close(1000, 'Manual close')
    
    def register_symbols(self, symbols, uid):
        tokens = []
        trading_symbols = []
        for symbol in symbols:
            zerodha_symbol = Instruments.get_ticker_subscription_format(symbol, uid)
            if not zerodha_symbol:
                logging.info(f'Token not found for symbol: {symbol}')
                trading_symbols.append(None)
                continue
            token = zerodha_symbol['token']
            tokens.append(token)
            trading_symbols.append(zerodha_symbol['trading_symbol'])
        self.ticker.subscribe(tokens)
        logging.info(f'Registered: {trading_symbols}')
    
    def unregister_symbols(self, symbols):
        tokens = []
        trading_symbols = []
        for symbol in symbols:
            symbol['broker'] = 'zerodha'
            zerodha_symbol = Instruments.change_symbol_to_broker_format(symbol)
            if not zerodha_symbol:
                logging.info(f'Token not found for symbol: {symbol}')
                trading_symbols.append(None)
                continue
            token = zerodha_symbol['token']
            tokens.append(token)
            trading_symbol = zerodha_symbol['trading_symbol']
            trading_symbols.append(trading_symbol)
            ZerodhaTicker.token_to_trading_symbol_map[token] = trading_symbol
        self.ticker.unsubscribe(tokens)
        logging.info(f'Unregistered: {trading_symbols}')
        return trading_symbols
    
    def on_ticks(self, ws, broker_ticks):
        ticks = []
        for tick in broker_ticks:
            trading_symbol = ZerodhaTicker.token_to_trading_symbol_map[tick['instrument_token']]
            if trading_symbol:
                # t = datetime.datetime.now()
                # t = (time.mktime(t.timetuple()))
                tick_data = TickData(trading_symbol)
                tick_data.add_zerodha_data(tick)
                # tick.received_time = time_received
                # self.tick_queue.append(tick)
                ticks.append(tick_data)
        
        self.on_new_ticks(ticks)

    def on_connect(self):
        self.onConnect()
    
    def on_close(self, ws, code, reason):
        self.onDisconnect(code, reason)
    
    def on_error(self, ws, code, reason):
        self.onError(code, reason)
    
    def on_reconnect(self, ws, attemptsCount):
        self.onReconnect(attemptsCount)
    
    def on_noreconnect(self, ws):
        self.on_max_reconnects_attempt()
    
    def on_order_update(self, ws, data):
        self.onOrderUpdate(data)
    



    