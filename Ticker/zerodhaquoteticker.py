import logging
import threading
import datetime
import time
from Ticker.baseticker import BaseTicker
from BrokerController.brokercontroller import BrokerController
from Instruments.instruments import Instruments
from Models.tickdata import TickData
from Utils.utils import get_market_start_time, get_market_end_time

class ZerodhaQuoteTicker(BaseTicker):
    __instance = None
    broker_handle = None
    ticker = None
    ticker_list = []
    subscription_flag = 0
    stop_ticker_ = 0

    @staticmethod
    def get_instance():
        if not ZerodhaQuoteTicker.__instance:
            return ZerodhaQuoteTicker()
        return ZerodhaQuoteTicker.__instance
    
    def __init__(self):
        if ZerodhaQuoteTicker.__instance:
            raise Exception('This class is a singleton!')
        else:
            ZerodhaQuoteTicker.__instance = self
        
        super().__init__('ZerodhaQuoteTicker')

        self.start_time = get_market_start_time()
        self.end_time = get_market_end_time()
    
    def register_symbols(self, symbols, uid):
        for symbol in symbols:
            trading_symbol = Instruments.get_trading_symbol(symbol, uid)
            if trading_symbol is None:
                logging.info(f'Trading symbol not found for symbol: {symbol}')
                continue
            trading_symbol = symbol['exchange'] + ':' + trading_symbol
            ZerodhaQuoteTicker.ticker_list.append(trading_symbol)

    def start_ticker(self):
        try:
            uid = BrokerController.broker_ticker_uid['jugaadtrader']
        except Exception as e:
            logging.exception(f'Not logged into jugaadtrader ticker account due to: {str(e)}')
            return
        
        self.broker_handle = BrokerController.get_broker_handle_uid(uid)
        ZerodhaQuoteTicker.stop_ticker_ = 0
        
        logging.info('Going to start ZerodhaQuoteTicker...')
        threading.Thread(target=self.run_ticker).start()
    
    def run_ticker(self):

        old_price_data_dict = None
        while True:
            now = datetime.datetime.now()
            if now > self.end_time or ZerodhaQuoteTicker.stop_ticker_:
                break

            if not ZerodhaQuoteTicker.ticker_list:
                if not ZerodhaQuoteTicker.subscription_flag:
                    print('No tickers in ZerodhaQuoteTicker subscribed list')
                    logging.info('No tickers in ZerodhaQuoteTicker subscribed list')
                    ZerodhaQuoteTicker.subscription_flag = 1
                time.sleep(0.5)
                continue
            ZerodhaQuoteTicker.subscription_flag = 0

            try:
                data = self.broker_handle.ltp(ZerodhaQuoteTicker.ticker_list)
                print(data)
            except Exception as e:
                logging.exception('Unable to pull data from Zerodha through Jugaadtrader')
                time.sleep(1)
                continue
            
            price_data_dict = {}            
            ticks = []
            for ticker in data:
                trading_symbol = ticker.split(':')[-1]
                tick = TickData(trading_symbol)
                tick.last_traded_price = data[ticker]['last_price']
                price_data_dict[ticker.split(':')[-1]] = data[ticker]['last_price']
                ticks.append(tick)
            
            if price_data_dict == old_price_data_dict:
                print('Alert! Check ZerodhaQuoteTicker!')
                logging.debug('Alert! Check ZerodhaQuoteTicker!')
                time.sleep(1)
                continue
            
            # self.on_new_ticks(ticks)
            for tick in ticks:
                print(tick)
            old_price_data_dict = price_data_dict
            time.sleep(1)

    def stop_ticker(self):
        logging.info('Stopping ZerodhaQuoteTicker...')
        ZerodhaQuoteTicker.stop_ticker_ = 1




        


