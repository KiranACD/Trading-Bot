import os
import logging
import time
import json
import datetime
from collections import defaultdict

# from Config.config import getserverconfig
# from core.Controller import Controller - This will not be required
from User.user import User
from BrokerController.brokercontroller import BrokerController
from Ticker.zerodhaticker import ZerodhaTicker
from Ticker.fyersticker import FyersTicker
from Trademanagement.trade import Trade
from Trademanagement.tradeexitreason import TradeExitReason
from Trademanagement.tradeencoder import TradeEncoder
from Trademanagement.tradestate import TradeState
from Ordermanagement.zerodhaordermanager import ZerodhaOrderManager
from Ordermanagement.orderinputparams import OrderInputParams
from Ordermanagement.ordermodifyparams import OrderModifyParams
from Ordermanagement.order import Order
from Models.ordertype import OrderType
from Models.orderstatus import OrderStatus
from Models.direction import Direction
from Instruments.instruments import Instruments
from Quotes.quotes import Quotes

from Utils import utils
from Config import config

class TradeManager:
    ticker = None
    users = []
    trades = []
    strategy_to_instance_map = {}
    symbol_to_cmp_map = {}
    intraday_trades_dir = None
    registered_symbols = []

    @staticmethod
    def run():
        if utils.is_today_holiday():
            logging.info('Cannot start Trademanager as today is trading holiday')
            return
        
        if utils.is_market_closed_for_the_day():
            logging.info('Cannot start Trademanager as market is closed for the day.')
            return
        
        # Register the users in the trademanager
        users_uid = config.get_users()
        for uid in users_uid:
            user_obj = User(uid)
            # Test each user object to check if login is a success. Make a profile call.
            if user_obj.test_broker_handle():
                TradeManager.users.append(user_obj)
            else:
                logging.info(f'{user_obj.uid} not logged in.')
                continue
        
        for broker in BrokerController.brokers:
            Instruments.fetch_instruments(broker)
            
        utils.wait_till_market_opens('Trade Manager')

        server_config = config.get_server_config()
        trades_dir = os.path.join(server_config['root'], 'trades')
        TradeManager.intraday_trades_dir = os.path.join(trades_dir, utils.get_today_date_str())
        if os.path.exists(TradeManager.intraday_trades_dir) is False:
            logging.info('TradeManager: Intraday trades directory %s does not exist. Hence going to create.', TradeManager.intraday_trades_dir)
            os.makedirs(TradeManager.intraday_trades_dir)

        ticker_broker_name = config.get_server_config()['ticker_broker']
        if ticker_broker_name == 'zerodha':
            TradeManager.ticker = ZerodhaTicker()
        elif ticker_broker_name == 'fyers':
            TradeManager.ticker = FyersTicker()
        
        ticker_uid = BrokerController.get_ticker_broker_uid(ticker_broker_name)
        TradeManager.ticker.start_ticker(ticker_uid)
        TradeManager.ticker.register_listener(TradeManager.ticker_listener)

        time.sleep(5)

        TradeManager.load_all_trades_from_file()

        while True:
            if utils.is_market_closed_for_day():
                logging.info('TradeManager: Stopping TradeManager as market closed.')
                break
            
            try:
                TradeManager.fetch_and_update_all_trade_orders()
                TradeManager.track_and_update_all_trades()
            except Exception as e:
                logging.exception('Exception in TradeManager main thread.')
            
            TradeManager.save_all_trades_to_file()

            time.sleep(30)
            logging.info('TradeManager: Main thread woke up...')
    
    @staticmethod
    def register_strategy(strategy_instance):
        TradeManager.strategy_to_instance_map[strategy_instance.get_name()] = strategy_instance
    
    @staticmethod
    def load_all_trades_from_file():
        trades_file_path = os.path.join(TradeManager.intraday_trades_dir, 'trades.json')
        if os.path.exists(trades_file_path) is False:
            logging.warn('TradeManager: Trades filepath %s does not exist', trades_file_path)
            return
        TradeManager.trades = []
        config.rea
        with open(trades_file_path, 'r') as tfile:
            trades_data = json.loads(tfile)
        
        for tr in trades_data:
            trade = TradeManager.convert_json_to_trade(tr)
            logging.info('loading trades from trade file: %s', trade)
            TradeManager.trades.append(trade)
            if trade.trading_symbol not in TradeManager.registered_symbols:
                TradeManager.ticker.register_symbols([trade.trading_symbol])
                TradeManager.registered_symbols.append(trade.trading_symbol)
            
        logging.info('TradeManager: Successfully loaded %d trades from json file %s', len(TradeManager.trades), trades_file_path)
    
    @staticmethod
    def save_all_trades_to_file():
        trades_file_path = os.path.join(TradeManager.intraday_trades_dir, 'trades.json')
        config.write_json(TradeManager.trades, trades_file_path, cls=TradeEncoder)
        logging.info('TradeManager: Saved %d trades to file %s', len(TradeManager.trades), trades_file_path)
    
    @staticmethod
    def add_new_trade(trade):
        if trade is None:
            return
        logging.info('TradeManager: add_new_trade called for %s', trade)
        for tr in TradeManager.trades:
            if tr.equals(trade):
                logging.warn('TradeManager: Trade already exists so not adding again. %s', trade)
                return
        TradeManager.trades.append(trade)
        logging.info('TradeManager: trade %s added successfully to the list', trade.trade_id)
        if trade.trading_symbol not in TradeManager.registered_symbols:
            TradeManager.ticker.register_symbols([trade.trading_symbol])
            TradeManager.registered_symbols.append(trade.trading_symbol)
        strategy_instance = TradeManager.strategy_to_instance_map[trade.strategy]
        if strategy_instance:
            strategy_instance.add_trade_to_list(trade)
    
    @staticmethod
    def disable_trade(trade, reason):
        if trade:
            logging.info('TradeManager: Going to disable trade id %s with th reason %s', trade.trade_id, reason)
            trade.tradestate = TradeState.DISABLED
    
    @staticmethod
    def ticker_listener(tick):
        TradeManager.symbol_to_cmp_map[tick.trading_symbol] = tick.last_traded_price
        for strategy in TradeManager.strategy_to_instance_map:
            long_trade = TradeManager.get_untriggered_trade(tick.trading_symbol, strategy, Direction.LONG)
            short_trade = TradeManager.get_untriggered_trade(tick.trading_symbol, strategy, Direction.SHORT)
            if long_trade is None and short_trade is None:
                continue
            strategy_instance = TradeManager.strategy_to_instance_map[strategy]
            if long_trade:
                if strategy_instance.should_place_trade(long_trade, tick):
                    is_success = TradeManager.execute_trade(long_trade)
                    if is_success:
                        long_trade.tradestate = TradeState.ACTIVE
                        long_trade.start_timestamp = utils.get_epoch()
                        continue
            
            if short_trade:
                if strategy_instance.should_place_trade(short_trade, tick):
                    is_sucess = TradeManager.execute_trade(short_trade)
                    if is_success:
                        short_trade.tradestate = TradeState.ACTIVE
                        short_trade.start_timestamp = utils.get_epoch()
                        continue
    
    @staticmethod
    def get_untriggered_trade(trading_symbol, strategy, direction):
        trade = None
        for tr in TradeManager.trades:
            if tr.tradestate == TradeState.DISABLED:
                continue
            if tr.tradestate != TradeState.CREATED:
                continue
            if tr.trading_symbol != trading_symbol:
                continue
            if tr.strategy != strategy:
                continue
            if tr.direction != direction:
                continue
            trade = tr
            break
        return trade
    
    @staticmethod
    def execute_trade(trade):
        logging.info('TradeManager: Execute trade called for %s', trade)
        trade.initial_stoploss = trade.stoploss
        oip = OrderInputParams(trade.trading_symbol)
        oip.direction = trade.direction
        oip.product_type = trade.product_type
        oip.order_type = OrderType.MARKET if trade.place_market_order is True else OrderType.LIMIT
        oip.price = trade.requested_entry
        oip.quantity = trade.quantity
        if trade.is_futures is True or trade.is_options is True:
            oip.is_fno = True
        try:
            trade.entry_order = TradeManager.get_order_manager(trade.uid).place_order(oip)
        except Exception as e:
            logging.error('TradeManager: Execute trade failed for trade_id %s: Error => %s', trade.trade_id, str(e))
            return False
        
        logging.info('TradeManager: Execute trade successful for %s and entry order %s', trade, trade.entry_order)
        return True


    @staticmethod
    def fetch_and_update_all_trade_orders():
        all_orders = defaultdict(list)
        for trade in TradeManager.trades:
            if trade.entry_order:
                all_orders[trade.uid].append(trade.entry_order)
            if trade.sl_order:
                all_orders[trade.uid].append(trade.sl_order)
            if trade.target_order:
                all_orders[trade.uid].append(trade.target_order)
        
        for user in all_orders:
            TradeManager.get_order_manager(user).fetch_and_update_order_details(all_orders[user])
    
    @staticmethod
    def track_and_update_all_trades():
        for trade in TradeManager.trades:
            if trade.tradestate == TradeState.ACTIVE:
                TradeManager.track_entry_order(trade)
                TradeManager.track_sl_order(trade)
                TradeManager.track_target_order(trade)
                if trade.intraday_squareoff_timestamp:
                    now_epoch = utils.get_epoch()
                    if now_epoch >= trade.intraday_squareoff_timestamp:
                        TradeManager.squareoff_trade(trade, TradeExitReason.SQUARE_OFF)
    
    @staticmethod
    def track_entry_order(trade):
        if trade.tradestate != TradeState.ACTIVE:
            return
        if trade.entry_order is None:
            return
        if trade.entry_order.order_status == OrderStatus.CANCELLED or trade.entry_order.order_status == OrderStatus.REJECTED:
            trade.tradestate = TradeState.CANCELLED
        trade.filled_quantity = trade.entry_order.filled_quantity
        if trade.filled_quantity > 0:
            trade.entry = trade.entry_order.average_price
        trade.cmp = TradeManager.symbol_to_cmp_map[trade.trading_symbol]
        utils.calculate_trade_pnl(trade)
    
    @staticmethod
    def track_sl_order(trade):
        if trade.tradestate != TradeState.ACTIVE:
            return
        if trade.stoploss == 0:
            return
        if trade.sl_order is None:
            TradeManager.place_sl_order(trade)
        else:
            if trade.sl_order.order_status == OrderStatus.COMPLETE:
                exit = trade.sl_order.average_price
                exit_reason = TradeExitReason.SL_HIT if trade.initial_stoploss == trade.stoploss else TradeExitReason.TRAIL_SL_HIT
                TradeManager.set_trade_to_complete(trade, exit, exit_reason)
                TradeManager.cancel_target_order(trade)
            
            elif trade.sl_order.order_status == OrderStatus.CANCELLED:
                logging.error('SL order %s for tradeID %s cancelled outside of algo. Setting the trade as completed with exit price as current market price.', trade.sl_order.order_id, trade.trade_id)
                exit = TradeManager.symbol_to_cmp_map[trade.trading_symbol]
                TradeManager.set_trade_to_complete(trade, exit, TradeExitReason.SL_CANCELLED)
                TradeManager.cancel_target_order(trade)
            
            else:
                TradeManager.check_and_update_trailsl(trade)
    
    @staticmethod
    def check_and_update_trailsl(trade):
        strategy_instance = TradeManager.strategy_to_instance_map[trade.strategy]
        if strategy_instance is None:
            return
        new_trail_sl = strategy_instance.get_trailing_sl(trade)
        update_sl = False
        if new_trail_sl > 0:
            if trade.direction == Direction.LONG and new_trail_sl > trade.stoploss:
                update_sl = True
            elif trade.direction == Direction.SHORT and new_trail_sl < trade.stoploss:
                update_sl = True
        if update_sl:
            omp = OrderModifyParams()
            omp.new_trigger_price = new_trail_sl
            try:
                old_sl = trade.stoploss
                TradeManager.get_order_manager(trade.uid).modify_order(trade.sl_order, omp)
                logging.info('TradeManager: Trail SL: Successfully modified stoploss from %f to %f for tradeID: %s', old_sl, new_trail_sl, trade.trade_id)
                trade.stoploss = new_trail_sl
            except Exception as e:
                logging.error('TradeManager: Failed to modify SL order for tradeID %s orderID %s: Error => %s', trade.trade_id, trade.sl_order, str(e))
    
    @staticmethod
    def track_target_order(trade):
        if trade.tradestate != TradeState.ACTIVE:
            return
        if trade.target == 0:
            return
        if trade.target_order is None:
            TradeManager.place_target_order(trade)
        else:
            if trade.target_order.order_status == OrderStatus.COMPLETE:
                exit = trade.target_order.average_price
                TradeManager.set_trade_to_complete(trade, exit, TradeExitReason.TARGET_HIT)
                TradeManager.cancel_sl_order(trade)
            elif trade.target_order.order_status == OrderStatus.CANCELLED:
                logging.error('Target order %s for tradeID %s cancelled outside of algo. Setting the trade as completed with exit price as current market price.', trade.target_order.order_id, trade.trade_id)
                exit = TradeManager.symbol_to_cmp_map[trade.trading_symbol]
                TradeManager.set_trade_to_complete(trade, exit, TradeExitReason.TARGET_CANCELLED)
                TradeManager.cancel_sl_order(trade)
    
    @staticmethod
    def place_sl_order(trade):
        oip = OrderInputParams(trade.trading_symbol)
        oip.direction = Direction.SHORT if trade.direction == Direction.LONG else Direction.LONG
        oip.product_type = trade.product_type
        oip.order_type = OrderType.SL_MARKET
        oip.trigger_price = trade.stoploss
        oip.quantity = trade.quantity
        if trade.is_futures is True or trade.is_options is True:
            oip.is_fno = True
        try:
            trade.sl_order = TradeManager.get_order_manager(trade.uid).place_order(oip)
        except Exception as e:
            logging.error('TradeManager: Failed to place SL order for tradeID %s: Error => %s', trade.trade_id, str(e))
            return False
        logging.info('TradeManager: Successfully placed SL order %s for tradeID %s', trade.sl_order.order_id, trade.trade_id)
        return True
    
    @staticmethod
    def place_target_order(trade, is_market_order=False):
        oip = OrderInputParams(trade.trading_symbol)
        oip.direction = Direction.SHORT if trade.direction == Direction.LONG else Direction.LONG
        oip.product_type = trade.product_type
        oip.order_type = OrderType.MARKET if is_market_order == True else OrderType.LIMIT
        oip.price = 0 if is_market_order is True else trade.target
        oip.quantity = trade.quantity
        if trade.is_futures is True or trade.is_options is True:
            oip.is_fno = True
        try:
            trade.target_order = TradeManager.get_order_manager(trade.uid).place_order(oip)
        except Exception as e:
            logging.error('TradeManager: Failed to place target order for tradeID %s: Error => %s', trade.trade_id, str(e))
            return False
        logging.info('TradeManager: Successfully placed target order %s for tradeID %s', trade.target_order.order_id, trade.trade_id)
        return True
    
    @staticmethod
    def cancel_entry_order(trade):
        if trade.entry_order:
            return
        if trade.entry_order.order_status == OrderStatus.CANCELLED:
            return
        try:
            TradeManager.get_order_manager(trade.uid).cancel_order(trade.entry_order)
        except Exception as e:
            logging.error('TradeManager: Failed to cancel entry order %s for trade_id %s: Error => %s', trade.entry_order.order_id, trade.trade_id, str(e))
        logging.info('TradeManager: Successfully cancelled entry order %s for trade_id %s', trade.entry_order.order_id, trade.trade_id)
    
    @staticmethod
    def cancel_sl_order(trade):
        if trade.sl_order is None:
            return
        if trade.sl_order.order_status == OrderStatus.CANCELLED:
            return
        try:
            TradeManager.get_order_manager(trade.uid).cancel_order(trade.sl_order)
        except Exception as e:
            logging.error('TradeManager: Failed to cancel SL order %s for tradeID %s: Error => %s', trade.sl_order.order_id, trade.trade_id, str(e))
        logging.info('TradeManager: Successfully cancelled SL order %s for tradeID %s', trade.sl_order.order_id, trade.trade_id)
    
    @staticmethod
    def cancel_target_order(trade):
        if trade.target_order is None:
            return
        if trade.target_order.order_status == OrderStatus.CANCELLED:
            return
        try:
            TradeManager.get_order_manager(trade.uid).cancel_order(trade.target_order)
        except Exception as e:
            logging.error('TradeManager: Failed to cancel target order %s for tradeID %s: Error => %s', trade.target_order.order_id, trade.trade_id, str(e))
        logging.info('TradeManager: Successfully cancelled target order %s for tradeID %s', trade.target_order.order_id, trade.trade_id)
    
    @staticmethod
    def set_trade_to_be_complete(trade, exit, exit_reason=None):
        trade.tradestate = TradeState.COMPLETED
        trade.exit = exit
        trade.exitreason = exit_reason if trade.exitreason is None else trade.exitreason
        trade.end_timestamp = utils.get_epoch()
        trade = utils.calculate_trade_pnl(trade)
        logging.info('TradeManager: setTradeToComplete strategy = %s, symbol = %s, qty = %d, entry = %f, exit = %f, pnl = %f, exit_reason = %s', trade.strategy, trade.trading_symbol, trade.filled_quantity, trade.entry, trade.exit, trade.pnl, trade.exitreason)
    
    @staticmethod
    def squareoff_trade(trade, reason=TradeExitReason.SQUARE_OFF):
        logging.info('TradeManager: squareoffTrade called for tradeID %s with reason %s', trade.trade_id, reason)
        if trade is None or trade.tradestate != TradeState.ACTIVE:
            return
        trade.exitreason = reason
        if trade.entry_order:
            if trade.entry_order.order_status == OrderStatus.OPEN:
                TradeManager.cancel_entry_order(trade)
        if trade.sl_order:
            TradeManager.cancel_sl_order(trade)
        if trade.target_order:
            logging.info('TradeManager: changing target order %s to MARKET to exit position for tradeID %s', trade.target_order.order_id, trade.trade_id)
            TradeManager.get_order_manager(trade.uid).modify_order_to_market(trade.target_order)
        else:
            logging.info('TradeManager: placing new order to exit position for tradeID %s', trade.trade_id)
            TradeManager.place_target_order(trade, True)
    
    @staticmethod
    def get_order_manager(uid):
        return BrokerController.get_order_manager(uid)
    
    @staticmethod
    def get_number_of_trades_placed_by_strategy(strategy):
        count = 0
        for trade in TradeManager.trades:
            if trade.strategy != strategy:
                continue
            if trade.tradestate == TradeState.CREATED or trade.tradestate == TradeState.DISABLED:
                continue
            count += 1
        return count
    
    @staticmethod
    def get_all_trades_by_strategy(strategy):
        trades_by_strategy = []
        for trade in TradeManager.trades:
            if trade.strategy == strategy:
                trades_by_strategy.append(trade)
        return trades_by_strategy
    
    @staticmethod
    def convert_json_to_trade(jsondata):
        trade = Trade(jsondata['trading_symbol'])
        trade.trade_id = jsondata['trade_id']
        trade.broker = jsondata['broker']
        trade.uid = jsondata['uid']
        trade.strategy = jsondata['strategy']
        trade.direction = jsondata['direction']
        trade.product_type = jsondata['product_type']
        trade.is_futures = jsondata['is_futures']
        trade.is_options = jsondata['is_options']
        trade.option_type = jsondata['option_type']
        trade.place_market_order = jsondata['place_market_order']
        trade.intraday_square_off_timestamp = jsondata['intraday_square_off_timestamp']
        trade.requested_entry = jsondata['requested_entry']
        trade.entry = jsondata['entry']
        trade.quantity = jsondata['quantity']
        trade.filled_quantity = jsondata['filled_quantity']
        trade.initial_stoploss = jsondata['initial_stoploss']
        trade.stoploss = jsondata['stoploss']
        trade.target = jsondata['target']
        trade.cmp = jsondata['cmp']
        trade.tradestate = jsondata['tradestate']
        trade.timestamp = jsondata['timestamp']
        trade.create_timestamp = jsondata['create_timestamp']
        trade.start_timestamp = jsondata['start_timestamp']
        trade.end_timestamp = jsondata['end_timestamp']
        trade.pnl = jsondata['pnl']
        trade.pnl_percentage = jsondata['pnl_percentage']
        trade.exit = jsondata['exit']
        trade.exitreason = jsondata['exitreason']
        trade.exchange = jsondata['exchange']
        trade.entry_order = jsondata['entry_order']
        trade.sl_order = jsondata['sl_order']
        trade.target_order = jsondata['target_order']
        return trade
    
    @staticmethod
    def convert_json_to_order(jsondata):
        if jsondata is None:
            return None
        order = Order()
        order.trading_symbol = jsondata['trading_symbol']
        order.exchange = jsondata['exchange']
        order.product_type = jsondata['product_type']
        order.order_type = jsondata['order_type']
        order.price = jsondata['order_price']
        order.trigger_price = jsondata['trigger_price']
        order.quantity = jsondata['quantity']
        order.order_id = jsondata['order_id']
        order.order_status = jsondata['order_status']
        order.average_price = jsondata['average_price']
        order.filled_quantity = jsondata['filled_quantity']
        order.pending_quantity = jsondata['pending_quantity']
        order.orderplacetimestamp = jsondata['orderplacetimestamp']
        order.lastorderupdatetimestamp = jsondata['lastorderupdatetimestamp']
        order.message = jsondata['message']
        return order
    
    @staticmethod
    def get_tick_ltp(trading_symbol):
        try:
            return TradeManager.symbol_to_cmp_map[trading_symbol]
        except Exception as e:
            logging.error(f'{trading_symbol} not in symbolCMPmap.')
            return None
    
    @staticmethod
    def register_symbols(trading_symbols):
        if TradeManager.ticker is None:
            return
        if isinstance(trading_symbols, str):
            trading_symbols = [trading_symbols]
        TradeManager.ticker.register_symbols(trading_symbols)
        TradeManager.registered_symbols.extend(trading_symbols)
        return True
    
    @staticmethod
    def get_quote_ltp(symbol):
        if isinstance(symbol, dict):
            quote = Quotes.get_quote_symbol_dict(symbol)
        if quote is None:
            logging.error('Quote not available for %s', symbol)
            return
        return quote.last_traded_price
    
    @staticmethod
    def get_ltp_trade(trade):
        if trade.is_futures or trade.is_options:
            return Quotes.get_fno_quote(trade.trading_symbol, trade.uid)
        elif trade.is_currency:
            return Quotes.get_currency_quote(trade.trading_symbol, trade.uid)
        elif trade.is_commodity:
            return Quotes.get_commodity_quote(trade.trading_symbol, trade.uid)
        else:
            return Quotes.get_equity_quote(trade.trading_symbol, trade.uid)
            
