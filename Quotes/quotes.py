import logging
from BrokerController.brokercontroller import BrokerController
from Models.quote import Quote
from Instruments.instruments import Instruments

class Quotes:

    @staticmethod
    def get_fno_quote(symbol, uid):
        if isinstance(symbol, dict):
            trading_symbol = Instruments.get_key_for_quotes(symbol, uid)
            if trading_symbol is None:
                logging.error('Trading symbol not available for symbol: %s', symbol)
                return
        else:
            trading_symbol = symbol
        broker = BrokerController.get_broker_name_uid(uid)
        if broker == 'zerodha':
            broker_handle = BrokerController.get_broker_handle_uid(uid)
            key = f'NFO:{trading_symbol}'
            quote_response = broker_handle.quote(key)
            broker_quote = quote_response[key]
            quote = Quote(trading_symbol)
            quote = Quotes.fill_zerodha_quote(quote, broker_quote)
            return quote
        elif broker == 'jugaadtrader':
            broker_handle = BrokerController.get_broker_handle_uid(uid)
            key = f'NFO:{trading_symbol}'
            quote_response = broker_handle.quote(key)
            broker_quote = quote_response[key]
            quote = Quote(trading_symbol)
            quote = Quotes.fill_zerodha_quote(quote, broker_quote)
            return quote
        elif broker == 'fyers':
            broker_handle = BrokerController.get_broker_handle_uid(uid)
            key = trading_symbol
            data = {'symbols':key}
            quote_response = broker_handle.quotes(data)
            broker_quote = quote_response['d'][0]['v']
            quote = Quote(trading_symbol.split(':')[-1])
            quote = Quotes.fill_fyers_quote(quote, broker_quote)
            return quote
    
    @staticmethod
    def get_equity_quote(symbol, uid):
        if isinstance(symbol, dict):
            trading_symbol = Instruments.get_trading_symbol(symbol, uid)
            if trading_symbol is None:
                logging.error('Trading symbol not available for symbol: %s', symbol)
                return
        else:
            trading_symbol = symbol
        broker = BrokerController.get_broker_name_uid(uid)
        if broker == 'zerodha':
            broker_handle = BrokerController.get_broker_handle_uid(uid)
            key = f'NSE:{trading_symbol}'
            quote_response = broker_handle.quote(key)
            broker_quote = quote_response[key]
            quote = Quote(trading_symbol)
            quote = Quotes.fill_zerodha_quote(quote, broker_quote)
            return quote
        elif broker == 'fyers':
            broker_handle = BrokerController.get_broker_handle_uid(uid)
            key = trading_symbol
            data = {'symbols':key}
            quote_response = broker_handle.quotes(data)
            broker_quote = quote_response['d'][0]['v']
            quote = Quote(trading_symbol.split(':')[-1])
            quote = Quotes.fill_fyers_quote(quote, broker_quote)
            return quote

    @staticmethod
    def get_currency_quote(symbol, uid):
        if isinstance(symbol, dict):
            trading_symbol = Instruments.get_trading_symbol(symbol, uid)
            if trading_symbol is None:
                logging.error('Trading symbol not available for symbol: %s', symbol)
                return
        else:
            trading_symbol = symbol
        broker = BrokerController.get_broker_name_uid(uid)
        if broker == 'zerodha':
            broker_handle = BrokerController.get_broker_handle_uid(uid)
            key = f'CDS:{trading_symbol}'
            quote_response = broker_handle.quote(key)
            broker_quote = quote_response[key]
            quote = Quote(trading_symbol)
            quote = Quotes.fill_zerodha_quote(quote, broker_quote)
            return quote
        elif broker == 'fyers':
            broker_handle = BrokerController.get_broker_handle_uid(uid)
            key = trading_symbol
            data = {'symbols':key}
            quote_response = broker_handle.quotes(data)
            broker_quote = quote_response['d'][0]['v']
            quote = Quote(trading_symbol.split(':')[-1])
            quote = Quotes.fill_fyers_quote(quote, broker_quote)
            return quote

    @staticmethod
    def get_commodity_quote(symbol, uid):
        if isinstance(symbol, dict):
            trading_symbol = Instruments.get_trading_symbol(symbol, uid)
            if trading_symbol is None:
                logging.error('Trading symbol not available for symbol: %s', symbol)
                return
        else:
            trading_symbol = symbol
        broker = BrokerController.get_broker_name_uid(uid)
        if broker == 'zerodha':
            broker_handle = BrokerController.get_broker_handle_uid(uid)
            key = f'COM:{trading_symbol}'
            quote_response = broker_handle.quote(key)
            broker_quote = quote_response[key]
            quote = Quote(trading_symbol)
            quote = Quotes.fill_zerodha_quote(quote, broker_quote)
            return quote
        elif broker == 'fyers':
            broker_handle = BrokerController.get_broker_handle_uid(uid)
            key = trading_symbol
            data = {'symbols':key}
            quote_response = broker_handle.quotes(data)
            broker_quote = quote_response['d'][0]['v']
            quote = Quote(trading_symbol.split(':')[-1])
            quote = Quotes.fill_fyers_quote(quote, broker_quote)
            return quote

    @staticmethod
    def fill_zerodha_quote(quote, broker_quote):

        quote.last_traded_price = broker_quote['last_price']
        quote.last_traded_quantity = broker_quote['last_quantity']
        quote.avg_traded_price = broker_quote['average_price']
        quote.volume = broker_quote['volume']
        quote.total_buy_quantity = broker_quote['buy_quantity']
        quote.total_sell_quantity = broker_quote['sell_quantity']
        ohlc = broker_quote['ohlc']
        quote.open = ohlc['open']
        quote.high = ohlc['high']
        quote.low = ohlc['low']
        quote.close = ohlc['close']
        quote.change = broker_quote['net_change']
        quote.oi_day_high = broker_quote['oi_day_high']
        quote.oi_day_low = broker_quote['oi_day_low']
        quote.lower_circuit_limit = broker_quote['lower_circuit_limit']
        quote.upper_circuit_limit = broker_quote['upper_circuit_limit']
        return quote
    
    @staticmethod
    def fill_fyers_quote(quote, broker_quote):

        quote.last_traded_price = broker_quote['lp']
        cmd = broker_quote['cmd']
        quote.last_traded_quantity = cmd['v']
        quote.volume = broker_quote['volume']
        quote.open = cmd['o']
        quote.high = cmd['h']
        quote.low = cmd['l']
        quote.close = cmd['c']
        quote.change = broker_quote['ch']
        return quote