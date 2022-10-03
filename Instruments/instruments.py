import os
import logging
import json
import datetime
import pandas as pd
import numpy as np
from Config.config import write_json, write_pickle, get_instruments_json, read_pickle, read_json
from BrokerController.brokercontroller import BrokerController

class Instruments:
    instruments_metadata = {}
    instruments_list = {}
    symbol_to_instrument_map = {}
    token_to_instrument_map = {}

    @staticmethod
    def get_instruments_metadata():
        Instruments.instruments_metadata = get_instruments_json()
    
    @staticmethod
    def check_last_updated_date(broker):
        if not Instruments.instruments_metadata:
            Instruments.get_instruments_metadata()
        if broker not in Instruments.instruments_metadata:
            return False
        return Instruments.instruments_metadata[broker]['last_date_updated'] == str(datetime.datetime.today().date())

    @staticmethod
    def should_fetch_from_broker(broker):
        if not Instruments.check_last_updated_date(broker):
            logging.info(f'Getting instruments from {broker}!')
            return True
        else:
            logging.info(f'Getting {broker} instruments from saved file!')
            return False
    
    @staticmethod
    def load_instruments(broker):
        Instruments.instruments_list[broker] = pd.DataFrame(read_pickle(Instruments.instruments_metadata[broker]['location']))
    
    @staticmethod
    def save_instruments(broker):
        write_pickle(Instruments.instruments_list[broker], Instruments.instruments_metadata[broker]['location'])

    @staticmethod
    def update_instruments_metadata(broker):
        Instruments.instruments_metadata[broker]['last_date_updated'] = str(datetime.datetime.today().date())
        Instruments.instruments_metadata[broker]['location'] = f'ConfigFiles/{broker}_instruments.pickle'
        write_json(Instruments.instruments_metadata, 'ConfigFiles/instruments_config.json')

    @staticmethod
    def fetch_instruments_from_broker(broker):
        if broker == 'zerodha':
            return Instruments.fetch_instruments_from_zerodha()
        elif broker == 'jugaadtrader':
            return Instruments.fetch_instruments_from_jugaadtrader()
        elif broker == 'fyers':
            return Instruments.fetch_instruments_from_fyers()
    

    @staticmethod
    def fetch_instruments(broker):
        if Instruments.should_fetch_from_broker(broker):
            if not Instruments.fetch_instruments_from_broker(broker):
                exit(-2)
        else:
            Instruments.load_instruments(broker)

    @staticmethod
    def fetch_instruments_from_zerodha():
        broker_handle = None
        if 'zerodha' in BrokerController.instruments_broker_uid:
            uid = BrokerController.instruments_broker_uid['zerodha']
            broker_handle = BrokerController.brokerhandle_uid_details_map[uid]
        
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
            write_pickle(instruments, 'ConfigFiles/zerodha_instruments.pickle')
            Instruments.instruments_list['zerodha'] = pd.DataFrame(instruments)
            Instruments.update_instruments_metadata('zerodha')
            return True
        except Exception as e:
            logging.exception(f'Exception while fetching instruments from broker: {e}')
            return False
    
    @staticmethod
    def fetch_instruments_from_jugaadtrader():
        broker_handle = None
        if 'jugaadtrader' in BrokerController.instruments_broker_uid:
            uid = BrokerController.instruments_broker_uid['jugaadtrader']
            broker_handle = BrokerController.brokerhandle_uid_details_map[uid]
        
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
            write_pickle(instruments, 'ConfigFiles/jugaadtrader_instruments.pickle')
            Instruments.instruments_list['jugaadtrader'] = pd.DataFrame(instruments)
            Instruments.update_instruments_metadata('jugaadtrader')
            return True
        except Exception as e:
            logging.exception(f'Exception while fetching instruments from broker: {e}')
            return False
    
    @staticmethod
    def fetch_instruments_from_fyers():
        equity_derivatives_url = Instruments.instruments_metadata['fyers']['equity_derivatives_url']
        equity_cash_url = Instruments.instruments_metadata['fyers']['equity_cash_url']
        try:
            df = pd.read_csv(equity_derivatives_url, header=None)
        except Exception as e:
            logging.exception(f'Exception while fetching instruments from broker: {e}')
            return False
        df.columns = 'fy_token symbol_details exchange_instrument_type minimum_lot_size tick_size isin trading_session last_update_date expiry symbol_ticker exchange segment scrip_code symbol underlying_scrip_code strike option_type'.split()
        df['expiry'] = df['expiry'].apply(lambda x: datetime.datetime.fromtimestamp(x).date())
        df['instrument_type'] = df['symbol_details'].apply(lambda x: x.split()[-1])
        try:
            df2 = pd.read_csv(equity_cash_url, header=None)
        except Exception as e:
            logging.exception(f'Exception while fetching instruments from broker: {e}')
            return False
        df2.columns = 'fy_token symbol_details exchange_instrument_type minimum_lot_size tick_size isin trading_session last_update_date expiry symbol_ticker exchange segment scrip_code symbol underlying_scrip_code strike option_type'.split()
        df = df.append(df2)
        df['strike'] = np.where((df['strike'] == -1), 0, df['strike'])
        write_pickle(df, 'ConfigFiles/fyers_instruments.pickle')
        Instruments.instruments_list['fyers'] = df
        Instruments.update_instruments_metadata('fyers')
        return True

    @staticmethod
    def change_symbol_to_zerodha_format(symbol):
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
            token = int(token)
            trading_symbol = Instruments.get_zerodha_trading_symbol(token=token)
            zerodha_format = {}
            zerodha_format['token'] = token
            zerodha_format['trading_symbol'] = trading_symbol
            return zerodha_format
        except Exception as e:
            logging.exception(f'Zerodha instument token not found due to: {e}')
            return {}
    
    @staticmethod
    def change_symbol_to_fyers_format(symbol):
        try:
            df = Instruments.instruments_list['fyers']
        except Exception as e:
            print(f'Exception while looking up fyers instruments data: {e}')
            logging.exception(f'Exception while looking up fyers instruments data: {e}')
            return None        
        try:
            expiry = datetime.datetime.strptime(symbol['expiry'], '%d-%m-%Y')
            expiry = expiry.date()
            symbol_ticker = df[(df['symbol'] == symbol['name']) & 
                    (df['instrument_type'] == symbol['instrument_type']) &
                    (df['expiry'] == expiry) &
                    (df['strike'] == symbol['strike'])]['symbol_ticker'].iloc[0]
            return symbol_ticker
        except Exception as e:
            print(f'Fyers instument symbol ticker not found due to: {e}')
            logging.exception(f'Fyers instument symbol ticker not found due to: {e}')
            return None
    
    @staticmethod
    def get_ticker_subscription_format(symbol, uid):
        uid_details = BrokerController.uid_uid_details_map[uid]
        if uid_details['broker'] == 'zerodha':
            return Instruments.change_symbol_to_zerodha_format(symbol)
        elif uid_details['broker'] == 'jugaadtrader':
            return Instruments.get_jugaadtrader_trading_symbol(symbol=symbol)
        elif uid_details['broker'] == 'fyers':
            return Instruments.change_symbol_to_fyers_format(symbol)

    @staticmethod
    def get_key_for_quotes(symbol, uid):
        uid_details = BrokerController.uid_uid_details_map[uid]
        if uid_details['broker'] == 'zerodha' or uid_details['broker'] == 'jugaadtrader':
            return Instruments.get_trading_symbol(symbol, uid)
        elif uid_details['broker'] == 'fyers':
            return Instruments.get_fyers_quotes_symbol(symbol=symbol)

    @staticmethod
    def get_trading_symbol(symbol, uid):
        uid_details = BrokerController.uid_uid_details_map[uid]
        if uid_details['broker'] == 'zerodha':
            return Instruments.get_zerodha_trading_symbol(symbol=symbol)
        elif uid_details['broker'] == 'jugaadtrader':
            return Instruments.get_jugaadtrader_trading_symbol(symbol=symbol)
    
    @staticmethod
    def get_fyers_quotes_symbol(symbol=None):
        df = Instruments.instruments_list['fyers']
        if symbol:
            try:
                expiry = datetime.datetime.strptime(symbol['expiry'], '%d-%m-%Y')
                expiry = expiry.date()
                print(symbol)
                print(expiry)
                tradingsymbol = df[(df['symbol'] == symbol['name']) &
                                   (df['instrument_type'] == symbol['instrument_type']) &
                                   (df['expiry'] == expiry) &
                                   (df['strike'] == symbol['strike'])]['symbol_ticker'].iloc[0]
                return tradingsymbol
            except Exception as e:
                print(f'Fyers trading symbol not found due to: {e}')
                logging.exception(f'Fyers trading symbol not found due to: {e}')
                return None

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
    
    @staticmethod
    def get_jugaadtrader_trading_symbol(token=None, symbol=None):
        df = Instruments.instruments_list['jugaadtrader']
        if token:
            inst = df[df['instrument_token'] == token]
            try:
                return inst['tradingsymbol'].iloc[0]
            except Exception as e:
                logging.exception(f'Zerodha trading symbol for token {token} not found due to: {e}')
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
                logging.exception(f'Zerodha trading symbol symbol dict {symbol} not found due to: {e}')
                return None
    
    @staticmethod
    def get_lot_size(symbol, uid):
        uid_details = BrokerController.uid_uid_details_map[uid]
        if uid_details['broker'] == 'zerodha':
            return Instruments.get_zerodha_lot_size(symbol)
        elif uid_details['broker'] == 'jugaadtrader':
            return Instruments.get_jugaadtrader_lot_size(symbol)
    
    @staticmethod
    def get_zerodha_lot_size(symbol):
        df = Instruments.instruments_list['zerodha']
        try:
            return df[df['tradingsymbol']==symbol]['lot_size'].iloc[0]
        except Exception as e:
            logging.exception(f'Zerodha lot size not found for symbol: {symbol} due to: {e}')
            return 0
    
    @staticmethod
    def get_jugaadtrader_lot_size(symbol):
        df = Instruments.instruments_list['jugaadtrader']
        try:
            return df[df['tradingsymbol']==symbol]['lot_size'].iloc[0]
        except Exception as e:
            logging.exception(f'Jugaadtrader lot size not found for symbol: {symbol} due to: {e}')
            return 0
    
    @staticmethod
    def get_zerodha_instrument_token(symbol):
        df = Instruments.instruments_list['zerodha']
        try:
            return df[df['tradingsymbo']==symbol]['instrument_token'].iloc[0]
        except Exception as e:
            logging.exception(f'Zerodha instrument token not found for symbol: {symbol} due to: {e}')
            return None
    
    @staticmethod
    def get_jugaadtrader_instrument_token(symbol):
        df = Instruments.instruments_list['jugaadtrader']
        try:
            return df[df['tradingsymbol']==symbol]['instrument_token'].iloc[0]
        except Exception as e:
            logging.exception(f'Zerodha instrument token not found for symbol: {symbol} due to: {e}')
            return None

    
    
