from BrokerController.brokercontroller import BrokerController
from Instruments.instruments import Instruments
from Strategies.niftyshortstraddle import NiftyShortStraddle
from Config.config import get_users
from Trademanagement.trademanager import TradeManager
import datetime
import time
import pandas as pd
import numpy as np
import logging
import threading
from Utils.utils import get_epoch, get_expiry
from Config.config import get_server_config

def init_logging(filepath):
    format = '%(asctime)s: %(message)s'
    logging.basicConfig(filename=filepath, format=format, level = logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

server_config = get_server_config()
log_file_dir = server_config['logfiledir']

init_logging(log_file_dir + '/app.log')

def update_fractal_bands(df, lookback):
    s = -1 * lookback
    df = df.iloc[s:]
    # if self.currentfractalhigh:
    #     self.prevfractalhigh = self.currentfractalhigh
    # if self.currentfractallow:
    #     self.prevfractallow = self.currentfractallow
    
    length = len(df)
    mid = length//2
    highcount = 0
    lowcount = 0
    for i in range(length):
        if i == mid:
            continue
        if df['high'].iloc[mid] > df['high'].iloc[i]:
            highcount += 1
        if df['low'].iloc[mid] < df['low'].iloc[i]:
            lowcount += 1
    
    if highcount == length - 1:
        currentfractalhigh = df['high'].iloc[mid]
    else:
        currentfractalhigh = None

    if lowcount == length - 1:
        currentfractallow = df['low'].iloc[mid]
    else:
        currentfractallow = None
    
    return currentfractalhigh, currentfractallow

def update_supertrend(df, lookback, multiplier):
    s = (-1 * lookback) - 1
    # if self.currentsupertrendup:
    #     self.prevsupertrendup = self.currentsupertrendup
    # if self.currentsupertrenddown:
    #     self.prevsupertrenddown = self.currentsupertrenddown

    df = df.iloc[s:]
    med_price = get_med_price(df['high'], df['low'])
    atr = get_atr(df['high'], df['low'], df['close'], lookback)
    upper, lower = get_basic_bands(med_price, atr, multiplier)
    supertrend, dir, supertrendlong, supertrendshort = get_final_bands(df['close'], upper, lower)
    currentsupertrendup = supertrendlong.iloc[-1]
    currentsupertrenddown = supertrendshort.iloc[-1]
    return currentsupertrendup, currentsupertrenddown

def get_med_price(high, low):
    return (high+low)/2

def get_atr(high, low, close, lookback):
    tr0 = abs(high-low)
    tr1 = abs(high-close.shift())
    tr2 = abs(low-close.shift())
    tr = pd.concat((tr0, tr1, tr2), axis = 1).max(axis=1)
    atr = tr.ewm(alpha=1 / lookback, adjust=False, min_periods=lookback).mean()
    return atr

def get_basic_bands(med_price, atr, multiplier):
    matr = multiplier*atr
    upper = med_price+matr
    lower = med_price-matr
    return upper, lower

def get_final_bands(close, upper, lower):
    trend = pd.Series(np.full(close.shape, np.nan), index=close.index)
    dir_ = pd.Series(np.full(close.shape, 1), index=close.index)
    long = pd.Series(np.full(close.shape, np.nan), index=close.index)
    short = pd.Series(np.full(close.shape, np.nan), index=close.index)

    for i in range(1, close.shape[0]):
        if close.iloc[i] > upper.iloc[i-1]:
            dir_.iloc[i] = 1
        elif close.iloc[i] < lower.iloc[i-1]:
            dir_.iloc[i] = -1
        else:
            dir_.iloc[i] = dir_.iloc[i-1]
            if dir_.iloc[i] > 0 and lower.iloc[i] < lower.iloc[i-1]:
                lower.iloc[i] = lower.iloc[i-1]
            if dir_.iloc[i] < 0 and upper.iloc[i] > upper.iloc[i-1]:
                upper.iloc[i] = upper.iloc[i-1]
        
        if dir_.iloc[i] > 0:
            trend.iloc[i] = long.iloc[i] = lower.iloc[i]
        else:
            trend.iloc[i] = short.iloc[i] = upper.iloc[i]
    
    return trend, dir_, long, short

def update_rsi(df, lookback):
    s = (-1 * lookback) -1
    df = df.iloc[s:]
    ret = df['close'].diff()
    up_series = pd.Series(dtype=float)
    down_series = pd.Series(dtype=float)
    for r in ret:
        if r<0:
            up_series.loc[len(up_series)] = 0
            down_series.loc[len(down_series)] = r
        else:
            up_series.loc[len(up_series)] = r
            down_series.loc[len(down_series)] = 0
    down_series = down_series.abs()
    up_ewm = up_series.ewm(com=lookback-1, adjust=False).mean()
    down_ewm = down_series.ewm(com=lookback-1, adjust=False).mean()
    rs = up_ewm/down_ewm
    rsi = 100 - (100/(1+rs))
    currentrsi = rsi.iloc[-1]
    return currentrsi

def update_volumesma(df, lookback):
    s = (-1 * lookback)
    df = df.iloc[s:]
    vol = df['volume']
    volumesma = vol.mean()
    # current_volume = df['volume'].iloc[-1]
    return volumesma

# uid = get_users()
# for u in uid:
#     uid = uid[u]

# BrokerController.handle_broker_login(uid)
# kite = BrokerController.get_broker_handle_uid(uid['uid'])
# for broker in BrokerController.brokers:
#     Instruments.fetch_instruments(broker)
# time.sleep(3)

# df = Instruments.instruments_list['jugaadtrader']

# expiry = get_expiry('BANKNIFTY', 'current', 'FUT')
# symbol = NiftyShortStraddle.get_symbol_dict('BANKNIFTY', 'FUT', 0, expiry, 'MCX')
# tradingsymbol = Instruments.get_ticker_subscription_format(symbol, uid['uid'])
# token = Instruments.get_jugaadtrader_instrument_token(tradingsymbol) #GOLD22OCTFUT
# print(token)
# # last_checked_time = []
# # while True:
# #     from_date = datetime.datetime.today().date()
# #     to_date = datetime.datetime.today().date()
# #     interval = '5minute'
# #     df = pd.DataFrame(kite.historical_data(token, from_date, to_date, interval))
# #     if df['date'].iloc[-1] in last_checked_time:
# #         continue
# #     print(df.iloc[-10:-1])
# #     print(df.iloc[-1])
# #     last_checked_time.append(df['date'].iloc[-1])

# from_date = datetime.datetime.today().date()
# to_date = datetime.datetime.today().date()
# interval = '5minute'
# df = pd.DataFrame(kite.historical_data(token, from_date, to_date, interval))

# print(datetime.datetime.now())
# up, down = update_fractal_bands(df, 5)

# uptrend, downtrend = update_supertrend(df, 14, 3)

# rsi = update_rsi(df, 14)
# print(rsi)
# vol_sma = update_volumesma(df, 20)
# print(vol_sma)
# print(datetime.datetime.now())

logging.info('Starting Algo...')
tm = threading.Thread(target=TradeManager.run)
tm.start()

time.sleep(5)

expiry = get_expiry('BANKNIFTY', 'current', 'FUT')
print(expiry)
