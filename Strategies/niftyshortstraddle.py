import logging
import time
from datetime import datetime
import configparser
import math

from Models.producttype import ZerodhaProductType, FyersProductType
from Models.quote import Quote
from Quotes.quotes import Quotes
from Trademanagement.trademanager import TradeManager
from Instruments.instruments import Instruments
from BrokerController.brokercontroller import BrokerController
from Utils.utils import get_expiry
from Config.config import get_nifty_short_straddle_service_config

class NiftyShortStraddle:
    FUT_SYMBOL = None
    CE_TICKERS = {}
    PE_TICKERS = {}
    base = 0
    number_of_strikes = 0
    config = None
    
    @staticmethod
    def get_symbol_dict(name, instrument_type, strike, expiry):
        return {'name':name, 'instrument_type':instrument_type, 'strike':strike, 'expiry':expiry}

    @staticmethod
    def get_strikes_list(price):
        atm = (price//NiftyShortStraddle.base)*NiftyShortStraddle.base
        upper_bound = atm+(NiftyShortStraddle.base)*NiftyShortStraddle.number_of_strikes
        lower_bound = atm-(NiftyShortStraddle.base)*NiftyShortStraddle.number_of_strikes
        strikes_list = list(range(lower_bound, upper_bound+NiftyShortStraddle.base, NiftyShortStraddle.base))
        return strikes_list

    @staticmethod
    def populate_tickers():
        '''
        Takes the current underlying price and generates option ticker list, both CE and PE...
        ...10 strikes up and 10 strikes down.
        '''
        NiftyShortStraddle.config = get_nifty_short_straddle_service_config()
        NiftyShortStraddle.base = NiftyShortStraddle.config['base']
        NiftyShortStraddle.number_of_strikes = NiftyShortStraddle.config['number_of_strikes']
        uid = NiftyShortStraddle.config['uid']
        expiry = get_expiry('current', 'FUT')
        symbol = NiftyShortStraddle.get_symbol_dict('NIFTY', 'FUT', 0, expiry)
        NiftyShortStraddle.FUT_SYMBOL = Instruments.get_trading_symbol(symbol, uid)
        underlying_price = Quotes.get_fno_quote(NiftyShortStraddle.FUT_SYMBOL).last_traded_price
        strikes_list = NiftyShortStraddle.get_strikes_list(underlying_price)
        expiry = get_expiry('current', 'OPT')
        
        for strike in strikes_list:
            symbol = {'name':'NIFTY', 'instrument_type':'CE', 'expiry':expiry, 'strike':float(strike)} 
            ce_trading_symbol = Instruments.get_trading_symbol(symbol, uid)
            NiftyShortStraddle.CE_TICKERS[strike] = ce_trading_symbol
            symbol = {'name':'NIFTY', 'instrument_type':'PE', 'expiry':expiry, 'strike':float(strike)} 
            pe_trading_symbol = Instruments.get_trading_symbol(symbol, uid)
            NiftyShortStraddle.CE_TICKERS[strike] = pe_trading_symbol

    
    @staticmethod
    def init_tickers():
        pass

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
    def get_straddle_combination():
        uid = NiftyShortStraddle.config['uid']
        underlying_price = Quotes.get_fno_quote(NiftyShortStraddle.FUT_SYMBOL, uid).last_traded_price
        strike_combinations = NiftyShortStraddle.get_strike_combinations(underlying_price)
        expiry = get_expiry('current', 'OPT')

        premium_lowerbound = 10**9
        combination_ce_symbol = None
        combination_pe_symbol = None
        for combination in strike_combinations:
            if combination[0] not in NiftyShortStraddle.CE_TICKERS:
                symbol = {'name':'NIFTY', 'instrument_type':'CE', 'strike':float(combination[0]), 'expiry':expiry}
                ce_symbol = Instruments.get_trading_symbol(symbol, uid)
            else:
                ce_symbol = NiftyShortStraddle.CE_TICKERS[combination[0]]
            if combination[1] not in NiftyShortStraddle.PE_TICKERS:
                symbol = {'name':'NIFTY', 'instrument_type':'PE', 'strike':float(combination[1]), 'expiry':expiry}
                pe_symbol = Instruments.get_trading_symbol(symbol, uid)
            else:
                pe_symbol = NiftyShortStraddle.PE_TICKERS[combination[1]]
            
            ce_price = Quotes.get_fno_quote(ce_symbol, uid).last_traded_price
            pe_price = Quotes.get_fno_quote(pe_symbol, uid).last_traded_price

            premium_diff = round(abs(ce_price - pe_price))
            if premium_diff < premium_lowerbound:
                combination_ce_symbol = ce_symbol
                combination_pe_symbol = pe_symbol
                premium_lowerbound = premium_diff
            
            return combination_ce_symbol, combination_pe_symbol
    
    @staticmethod
    def get_straddle_combo_price(ce_symbol=None, pe_symbol=None):
        uid = NiftyShortStraddle.config['uid']
        ce_quote = Quotes.get_fno_quote(ce_symbol, uid)
        pe_quote = Quotes.get_fno_quote(pe_symbol, uid)
        if not ce_quote or not pe_quote:
            logging.error('Could not get quotes for option symbols %s and %s', ce_symbol, pe_symbol)
            return
        return (ce_quote.last_traded_price, pe_quote.last_traded_price)

            



    

