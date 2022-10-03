import logging
import json
import threading
from Models.tickdata import TickData
from Ticker.baseticker import BaseTicker
from BrokerController.brokercontroller import BrokerController
from Instruments.instruments import Instruments
from Config.config import get_server_config
from fyers_api.Websocket import ws
from fyers_api import fyersModel

class FyersTicker(BaseTicker):
    __instance = None

    @staticmethod
    def get_instance():
        if FyersTicker.__instance is None:
            FyersTicker()
        return FyersTicker.__instance
    
    def __init__(self):
        if FyersTicker.__instance is not None:
            raise Exception('This class is a singleton!')
        else:
            FyersTicker.__instance = self
        super().__init__('FyersTicker')
        self.data_type = 'symbolData'
    
    def start_ticker(self):
        try:
            uid = BrokerController.get_ticker_broker_uid('fyers')
        except Exception as e:
            logging.exception(f'Not logged in to fyers ticker account due to {e}')
            return

        uid_details = BrokerController.get_uid_details_uid(uid)
        access_token = uid_details['access_token']
        app_id = uid_details['app_id']
        access_token_webscoket = app_id + ':' + access_token
        log_file_path = get_server_config()['logfiledir']

        data_type = 'symbolData'
        ticker = ws.FyersSocket(access_token=access_token_webscoket, log_path=log_file_path)
        ticker.websocket_data = self.on_message
        self.ticker = ticker
        # self.ticker.keep_running()
    
    def register_symbols(self, symbols, uid):
        subscription_symbols = []
        print(symbols)
        for symbol in symbols:
            symbol_ticker = Instruments.get_ticker_subscription_format(symbol, uid)
            if not symbol_ticker:
                logging.error(f'FyersTicker: Could not find symbol ticker for {symbol}')
                continue
            subscription_symbols.append(symbol_ticker)
        self.ticker.subscribe(symbol=subscription_symbols, data_type=self.data_type)
        logging.info(f'Registered: {subscription_symbols}')
        print(f'Registered: {subscription_symbols}')
    
    def on_message(self, msg):
        ticks = []
        if msg:
            # print(f"Custom:{msg}")
            print(f'Type:{type(msg)}')
            for btick in msg:
                # print(btick)
                tick = TickData(btick['symbol'])
                print(tick)
                threading.Thread(target=tick.add_fyers_data,args=(btick,)).start()
                ticks.append(tick)
        print('here')
        threading.Thread(target=self.on_new_ticks,args=(ticks,)).start()
    


