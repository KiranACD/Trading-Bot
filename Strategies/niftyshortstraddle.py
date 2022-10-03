import logging
import math
import time
import datetime

from Quotes.quotes import Quotes
from Instruments.instruments import Instruments
from BrokerController.brokercontroller import BrokerController
from Utils.utils import get_expiry
from Config.config import get_nifty_straddle_service_config, get_server_config

class NiftyShortStraddle:
    FUT_SYMBOL = None
    FUT_SYMBOL_DICT = None
    CE_TICKERS = {}
    PE_TICKERS = {}
    symbol_dict_list = []
    base = 0
    number_of_strikes = 0
    config = None
    
    @staticmethod
    def get_symbol_dict(name, instrument_type, strike, expiry, exchange):
        return {'name':name, 'instrument_type':instrument_type, 'strike':strike, 'expiry':expiry, 'exchange':exchange}

    @staticmethod
    def get_strikes_list(price):
        atm = (price//NiftyShortStraddle.base)*NiftyShortStraddle.base
        upper_bound = atm+(NiftyShortStraddle.base)*NiftyShortStraddle.number_of_strikes
        lower_bound = atm-(NiftyShortStraddle.base)*NiftyShortStraddle.number_of_strikes
        strikes_list = list(range(int(lower_bound), int(upper_bound+NiftyShortStraddle.base), NiftyShortStraddle.base))
        return strikes_list

    @staticmethod
    def populate_tickers():
        '''
        Takes the current underlying price and generates option ticker list, both CE and PE...
        ...10 strikes up and 10 strikes down.
        '''
        NiftyShortStraddle.config = get_nifty_straddle_service_config()
        NiftyShortStraddle.base = int(NiftyShortStraddle.config['base'])
        NiftyShortStraddle.number_of_strikes = int(NiftyShortStraddle.config['number_of_strikes'])
        historical_broker = get_server_config()['historical_broker']
        uid = BrokerController.get_historical_broker_uid(historical_broker)
        NiftyShortStraddle.config['uid'] = uid
        start = datetime.datetime.now()
        while True:
            try:
                expiry = get_expiry('NIFTY', 'current', 'FUT')
                symbol = NiftyShortStraddle.get_symbol_dict('NIFTY', 'FUT', 0, expiry, 'NFO')
                NiftyShortStraddle.FUT_SYMBOL_DICT = symbol
                NiftyShortStraddle.FUT_SYMBOL = Instruments.get_key_for_quotes(symbol, uid)
                if NiftyShortStraddle.FUT_SYMBOL is None and (datetime.datetime.now() - start).seconds < 300:
                    continue
                break
            except Exception as e:
                if (datetime.datetime.now() - start).seconds > 300:
                    break
                logging.info(f'Instruments not yet available due to ==> {str(e)}')
                time.sleep(1)
        if NiftyShortStraddle.FUT_SYMBOL is None:
            logging.DEBUG('Unable to populate tickers as instruments not available and Futures symbol is none.')
            return
        logging.info('Set Nifty Futures Symbol')
        underlying_price = Quotes.get_fno_quote(NiftyShortStraddle.FUT_SYMBOL, uid).last_traded_price
        strikes_list = NiftyShortStraddle.get_strikes_list(underlying_price)
        expiry = get_expiry('NIFTY','current', 'OPT')

        for strike in strikes_list:
            symbol = NiftyShortStraddle.get_symbol_dict('NIFTY', 'CE', float(strike), expiry, 'NFO')
            # symbol = {'name':'NIFTY', 'instrument_type':'CE', 'expiry':expiry, 'strike':float(strike), 'exchange':'NFO'} 
            NiftyShortStraddle.symbol_dict_list.append(symbol)
            ce_trading_symbol = Instruments.get_key_for_quotes(symbol, uid)
            NiftyShortStraddle.CE_TICKERS[strike] = ce_trading_symbol
            symbol = NiftyShortStraddle.get_symbol_dict('NIFTY', 'PE', float(strike), expiry, 'NFO')
            NiftyShortStraddle.symbol_dict_list.append(symbol)
            pe_trading_symbol = Instruments.get_key_for_quotes(symbol, uid)
            NiftyShortStraddle.PE_TICKERS[strike] = pe_trading_symbol

    
    @staticmethod
    def init_service():
        NiftyShortStraddle.populate_tickers()

    @staticmethod
    def get_strike_combinations(price):
        base = NiftyShortStraddle.base
        price_up = math.ceil(price/base)*base
        price_down = math.floor(price/base)*base
        strike_combinations = [
        [price_down, price_down],
        [price_down - base, price_down - base],
        [price_down, price_down - base],
        [price_down, price_up],
        [price_up, price_up],
        [price_up, price_down],
        [price_up + base, price_up + base],
        [price_up + base, price_up]
        ]
        return strike_combinations

    @staticmethod
    def add_ticker(symbol):
        uid = NiftyShortStraddle.config['uid']
        if symbol['instrument_type'] == 'CE':
            ce_symbol = Instruments.get_key_for_quotes(symbol, uid)
            NiftyShortStraddle.CE_TICKERS[symbol['strike']] = ce_symbol
        else:
            pe_symbol = Instruments.get_key_for_quotes(symbol, uid)
            NiftyShortStraddle.PE_TICKERS[symbol['strike']] = pe_symbol

    @staticmethod
    def get_straddle_combination():
        uid = NiftyShortStraddle.config['uid']
        underlying_price = Quotes.get_fno_quote(NiftyShortStraddle.FUT_SYMBOL, uid).last_traded_price
        strike_combinations = NiftyShortStraddle.get_strike_combinations(underlying_price)
        expiry = get_expiry('NIFTY', 'current', 'OPT')

        premium_lowerbound = 10**9
        for combination in strike_combinations:
            ce_symbol_dict = NiftyShortStraddle.get_symbol_dict('NIFTY', 'CE', float(combination[0]), expiry, 'NFO')
            pe_symbol_dict = NiftyShortStraddle.get_symbol_dict('NIFTY', 'PE', float(combination[1]), expiry, 'NFO')
            if combination[0] not in NiftyShortStraddle.CE_TICKERS:
                # ce_symbol_dict = {'name':'NIFTY', 'instrument_type':'CE', 'strike':float(combination[0]), 'expiry':expiry}
                ce_symbol = Instruments.get_key_for_quotes(ce_symbol_dict, uid)
            else:
                ce_symbol = NiftyShortStraddle.CE_TICKERS[combination[0]]
            if combination[1] not in NiftyShortStraddle.PE_TICKERS:           
                pe_symbol = Instruments.get_key_for_quotes(pe_symbol_dict, uid)
            else:
                pe_symbol = NiftyShortStraddle.PE_TICKERS[combination[1]]
    
            ce_price = Quotes.get_fno_quote(ce_symbol, uid).last_traded_price
            pe_price = Quotes.get_fno_quote(pe_symbol, uid).last_traded_price

            premium_diff = round(abs(ce_price - pe_price))
            if premium_diff < premium_lowerbound:
                ce_dict = {'trading_symbol':ce_symbol,
                           'symbol_dict':ce_symbol_dict}
                pe_dict = {'trading_symbol':pe_symbol,
                           'symbol_dict':pe_symbol_dict}
                premium_lowerbound = premium_diff
            
        straddle_dict = {'ce':ce_dict, 'pe':pe_dict}
        return straddle_dict
    
    @staticmethod
    def get_straddle_combo_price(ce_symbol=None, pe_symbol=None):
        uid = NiftyShortStraddle.config['uid']
        ce_quote = Quotes.get_fno_quote(ce_symbol, uid)
        pe_quote = Quotes.get_fno_quote(pe_symbol, uid)
        if not ce_quote or not pe_quote:
            logging.error('Could not get quotes for option symbols %s and %s', ce_symbol, pe_symbol)
            return
        return (ce_quote.last_traded_price, pe_quote.last_traded_price)

            



    

