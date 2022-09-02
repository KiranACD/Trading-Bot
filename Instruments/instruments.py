import os
import logging
import json
import datetime
import pandas as pd

from Config import config
from Utils import utils, filesystem
from BrokerController.brokercontroller import BrokerController

class Instruments:
    instruments_metadata = {}
    instruments_list = {}
    symbol_to_instrument_map = {}
    token_to_instrument_map = {}

    @staticmethod
    def get_instruments_metadata():
        Instruments.instruments_metadata = config.get_instruments_json()
    
    @staticmethod
    def check_last_updated_date(broker):
        return Instruments.instruments_metadata[broker]['last_date_updated'] == str(datetime.datetime.today().date())

    @staticmethod
    def should_fetch_from_broker(broker):
        if Instruments.check_last_updated_date(broker):
            logging.info(f'Getting instruments from {broker}!')
            return True
        else:
            logging.info(f'Getting {broker} instruments from saved file!')
            return False
    
    @staticmethod
    def load_instruments(broker):
        Instruments.instruments_list[broker] = pd.DataFrame(filesystem.read_pickle(Instruments.instruments_metadata[broker]['location']))
    
    @staticmethod
    def save_instruments(broker):
        filesystem.write_pickle(Instruments.instruments_list[broker], Instruments.instruments_metadata[broker]['location'])

    @staticmethod
    def update_instruments_metadata(broker):
        Instruments.instruments_metadata[broker]['last_date_updated'] = str(datetime.datetime.today().date())
        Instruments.instruments_metadata[broker]['location'] = f'ConfigFiles/{broker}_instruments.pickle'
        filesystem.write_json(Instruments.instruments_metadata, 'ConfigFiles/instruments_config.json')

    @staticmethod
    def fetch_instruments_from_broker(broker):
        if broker == 'zerodha':
            Instruments.fetch_instruments_from_zerodha()
    

    @staticmethod
    def fetch_instruments(broker):
        if Instruments.should_fetch_from_broker(broker):
            if not Instruments.fetch_instruments_from_broker(broker):
                exit(-2)

    @staticmethod
    def fetch_instruments_from_zerodha():
        broker_handle = None
        if 'zerodha' in BrokerController.instruments_broker_handle:
            uid = BrokerController.broker_instruments_uid['zerodha']
            broker_handle = BrokerController.broker_uid_handle_map[uid]
        
        try:
            instruments = broker_handle.instruments()
            instruments = pd.DataFrame(instruments)
            expiry_instruments =            (
                instruments[instruments['expiry'] != ''].sort_values('expiry').copy()
            )
            non_expiry_instruments = (
                instruments[instruments['expiry'] == ''].sort_values('expiry').copy()
            )
            instruments = pd.concat([
                expiry_instruments,
                non_expiry_instruments
                ]).reset_index()
            filesystem.write_pickle(instruments, 'ConfigFiles/zerodha_instruments.pickle')
            Instruments.instruments_list['zerodha'] = pd.DataFrame(instruments)
            Instruments.update_instruments_metadata('zerodha')
            return True
        except Exception as e:
            logging.exception(f'Exception while fetching instruments from broker: {e}')
            return False
    
    @staticmethod
    def convert_symbol_to_zerodha_subscription_format(symbol):
        try:
            df = Instruments.instruments_list['zerodha']
        except Exception as e:
            logging.exception(f'Exception while looking up zerodha instruments data: {e}')
            return None        
        try:
            expiry = datetime.datetime.strptime(symbol['expiry'], '%d-%m-%Y')
            expiry = expiry.date()
            token = df[(df['name'] == symbol['name']) & 
                    (df['instrument_type'] == symbol['instrument_type']) &
                    (df['expiry'] == expiry) &
                    (df['strike'] == symbol['strike'])]['instrument_token'].iloc[0]
            return int(token)
        except Exception as e:
            logging.exception(f'Zerodha instument token not found due to: {e}')
            return None
    
    @staticmethod
    def get_trading_symbol(symbol, uid):
        uid_details = BrokerController.broker_uid_details_map[uid]
        if uid_details['broker'] == 'zerodha':
            return Instruments.get_zerodha_trading_symbol(symbol=symbol)
    
    @staticmethod
    def get_zerodha_trading_symbol(token=None, symbol=None):
        df = Instruments.instruments_list['zerodha']
        if token:
            inst = df[df['instrument_token'] == token]
            try:
                return inst['tradingsymbol'].iloc[0]
            except Exception as e:
                logging.exception(f'Zerodha trading symbol not found due to: {e}')
                return None
        
        if symbol:
            try:
                expiry = datetime.datetime.strptime(symbol['expiry'], '%d-%m-%Y')
                expiry = expiry.date()
                tradingsymbol = df[(df['name'] == symbol['name']) & 
                        (df['instrument_type'] == symbol['instrument_type']) &
                        (df['expiry'] == expiry) &
                        (df['strike'] == symbol['strike'])]['tradingsymbol'].iloc[0]
                return tradingsymbol
            except Exception as e:
                logging.exception(f'Zerodha trading symbol not found due to: {e}')
                return None
    
    
