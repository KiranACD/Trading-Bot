import logging
import datetime
import time
import uuid
import calendar
import math
from Instruments.instruments import Instruments
from Models.direction import Direction
from Trademanagement.tradestate import TradeState
from Config.config import get_holidays

dateformat = '%Y-%m-%d'
timeformat = '%H:%M:%S'
datetimeformat = '%Y-%m-%d %H:%M:%S'

def generate_trade_id():
    return str(uuid.uuid4())

def get_epoch(datetimeobj=None):
    if datetimeobj is None:
        datetimeobj = datetime.datetime.now()
    epoch = datetime.datetime.timestamp(datetimeobj)
    return int(epoch)

def convert_to_date_str(datetimeobj):
    return datetimeobj.strftime(dateformat)

def is_holiday(datetimeobj):
    return False
    # day_of_week = calendar.day_name[datetimeobj.weekday()]
    # if day_of_week == 'Saturday' or day_of_week == 'Sunday':
    #     return True
    
    # date_str = convert_to_date_str(datetimeobj)
    # holidays = get_holidays()
    # if (date_str in holidays):
    #     return True
    # else:
    #     return False

def is_today_holiday():
    return is_holiday(datetime.datetime.now())

def is_market_closed_for_day():
    if is_today_holiday():
        return True
    now = datetime.datetime.now()
    market_end_time = get_market_end_time()
    return now > market_end_time

def get_market_start_time(datetimeobj=None):
    return get_time_of_day(9, 15, 0, datetimeobj)

def get_market_end_time(datetimeobj=None):
    return get_time_of_day(23, 55, 0, datetimeobj)

def get_time_of_day(hours, minutes, seconds, datetimeobj=None):
    if datetimeobj is None:
        datetimeobj = datetime.datetime.now()
    datetimeobj = datetimeobj.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
    return datetimeobj

def get_time_of_today(hours, minutes, seconds):
    return get_time_of_day(hours, minutes, seconds, datetime.datetime.now())

def get_today_date_str():
    return convert_to_date_str(datetime.datetime.now())

def wait_till_market_opens(context):
    now_epoch = get_epoch(datetime.datetime.now())
    market_start_time_epoch = get_epoch(get_market_start_time())
    wait_seconds = market_start_time_epoch - now_epoch
    if wait_seconds > 0:
        logging.info('%s: Waiting for %d seconds till market opens...', context, wait_seconds)
        time.sleep(wait_seconds)

def round_off(price):
    return round(price, 2)

def calculate_trade_pnl(trade):
    if trade.tradestate == TradeState.ACTIVE:
        if trade.cmp > 0:
            if trade.direction == Direction.LONG:
                trade.pnl = round_off(trade.filled_quantity * (trade.cmp - trade.entry))
            else:
                trade.pnl = round_off(trade.filled_quantity * (trade.entry - trade.cmp))
    else:
        if trade.exit > 0:
            if trade.direction == Direction.LONG:
                trade.pnl = round_off(trade.filled_quantity * (trade.exit - trade.entry))
            else:
                trade.pnl = round_off(trade.filled_quantity * (trade.entry - trade.exit))
    trade_value = trade.entry * trade.filled_quantity
    if trade_value > 0:
        trade.pnl_percentage = round_off(trade.pnl * 100/trade_value)
    return trade

def round_to_nse_price(price):
    x = round(price, 2) * 20
    y = math.ceil(x)
    return y/20

def get_expiry(name, expiry_type, instrument_type):
    
    if expiry_type == 'current':
        expiry_offset = 0
    else:
        logging.info('Only current expiries available!')
        return
    if instrument_type == 'OPT':
        instrument_type = 'CE'
    if 'zerodha' in Instruments.instruments_list:
        df = Instruments.instruments_list['zerodha']
        expiry = df[(df['name'] == name) &
                    (df['instrument_type'] == instrument_type)]['expiry'].iloc[expiry_offset]
    elif 'jugaadtrader' in Instruments.instruments_list:
        df = Instruments.instruments_list['jugaadtrader']
        expiry = df[(df['name'] == name) &
                    (df['instrument_type'] == instrument_type)]['expiry'].iloc[expiry_offset]
    elif 'fyers' in Instruments.instruments_list:
        df = Instruments.instruments_list['fyers']
        expiry = df[(df['symbol'] == name) &
                    (df['instrument_type'] == instrument_type)]['expiry'].iloc[expiry_offset]
    else:
        logging.info('Zerodha instruments list not available.')
        return
    return datetime.datetime.strftime(expiry, '%d-%m-%Y')



