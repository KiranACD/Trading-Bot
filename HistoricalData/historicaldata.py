import logging
import pandas as pd
from Instruments.instruments import Instruments
from BrokerController.brokercontroller import BrokerController
from Config.config import get_server_config

class HistoricalData:

    broker = None
    broker_handle = None

    @staticmethod
    def get_historical_data_uid(symbol, from_date, to_date, timeframe):

        if HistoricalData.broker is None:
            HistoricalData.get_historical_broker()

        if isinstance(symbol, dict):
            trading_symbol = Instruments.get_trading_symbol(symbol)
            if trading_symbol is None:
                logging.error('Trading symbol not available for symbol: %s', symbol)
                return
        else:
            trading_symbol = symbol

        if HistoricalData.broker == 'zerodha' or HistoricalData.broker == 'jugaadtrader':
            token = Instruments.get_zerodha_instrument_token(symbol)
            if token is None:
                logging.error(f'Could get historical data for symbol {symbol} due to failed token retrieval')
                return
            try:
                data = pd.DataFrame(HistoricalData.broker_handle.historical_data(token, from_date, to_date, timeframe))
                return data
            except Exception as e:
                logging.error(f'Could not get historical data for symbol {symbol} from broker {HistoricalData.broker}')
                return None

    @staticmethod
    def get_historical_broker():
        HistoricalData.broker = get_server_config()['historical_data_broker']
        uid = BrokerController.get_historical_broker_uid(HistoricalData.broker)
        HistoricalData.broker_handle = BrokerController.get_broker_handle_uid(uid)

