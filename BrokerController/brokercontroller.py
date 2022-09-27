import logging
import datetime
from Loginmanagement.zerodhalogin import ZerodhaLogin
from Loginmanagement.jugaadTraderlogin import JugaadTradeLogin
from Config.config import write_json, get_users
from User.userencoder import UserEncoder
# from Ordermanagement.

class BrokerController:

    brokers = []
    brokerhandle_uid_details_map = {}
    uid_uid_details_map = {}
    broker_ticker_uid = {}
    broker_historical_uid = {}
    instruments_broker_uid = {}
    uid_order_manager_map = {}

    @staticmethod
    def handle_broker_login(uid):
        if uid['broker'] == 'zerodha':
            if uid['access_token_date'] == str(datetime.datetime.now().date()):
                broker_handle = ZerodhaLogin.set_broker_handle(uid)
            else:
                broker_handle = ZerodhaLogin.login(uid)
            logging.info(f'Logged into {uid["name"]} with user id {uid["account_username"]}')
            BrokerController.brokerhandle_uid_details_map[uid['uid']] = broker_handle
            BrokerController.uid_uid_details_map[uid['uid']] = uid
            if uid['ticker'] and 'zerodha' not in BrokerController.broker_ticker_uid:
                BrokerController.broker_ticker_uid['zerodha'] = uid['uid']
            if uid['historical_data'] and 'zerodha' not in BrokerController.broker_historical_uid:
                BrokerController.broker_historical_uid['zerodha'] = uid['uid']
            if 'zerodha' not in BrokerController.instruments_broker_uid:
                BrokerController.instruments_broker_uid['zerodha'] = uid['uid']
            if 'zerodha' not in BrokerController.brokers:
                BrokerController.brokers.append('zerodha')

        elif uid['broker'] == 'jugaadtrader':
            broker_handle = JugaadTradeLogin.login(uid)
            logging.info(f'Logged into {uid["name"]} with user id {uid["account_username"]}')
            BrokerController.brokerhandle_uid_details_map[uid['uid']] = broker_handle
            BrokerController.uid_uid_details_map[uid['uid']] = uid
            if uid['ticker'] and 'jugaadtrader' not in BrokerController.broker_ticker_uid:
                BrokerController.broker_ticker_uid['jugaadtrader'] = uid['uid']
            if uid['historical_data'] and 'jugaadtrader' not in BrokerController.broker_historical_uid:
                BrokerController.broker_historical_uid['jugaadtrader'] = uid['uid']
            if 'jugaadtrader' not in BrokerController.instruments_broker_uid:
                BrokerController.instruments_broker_uid['jugaadtrader'] = uid['uid']
            if 'jugaadtrader' not in BrokerController.brokers:
                BrokerController.brokers.append('jugaadtrader')
        
        BrokerController.save_user_details_to_json(uid)
    
    @staticmethod
    def get_ticker_accesscode(broker):
        if broker == 'zerodha' and broker in BrokerController.broker_ticker_uid:
            uid_id = BrokerController.broker_ticker_uid[broker]
            uid_details = BrokerController.uid_uid_details_map[uid_id]
            access_token = uid_details['access_token']
            return access_token
        return None
    
    @staticmethod
    def get_ticker_broker_uid(broker):
        if broker == 'zerodha' and broker in BrokerController.broker_ticker_uid:
            uid_id = BrokerController.broker_ticker_uid[broker]
            return uid_id
        return None
    
    @staticmethod
    def get_historical_broker_uid(broker):
        if broker == 'zerodha' and broker in BrokerController.broker_historical_uid:
            uid_id = BrokerController.broker_historical_uid[broker]
            return uid_id
        elif broker == 'jugaadtrader' and broker in BrokerController.broker_historical_uid:
            uid_id = BrokerController.broker_historical_uid[broker]
            return uid_id
        return None
    
    @staticmethod
    def get_instrument_handle(broker):
        if broker == 'zerodha' and broker in BrokerController.instruments_broker_uid:
            uid_id = BrokerController.instruments_broker_uid[broker]
            broker_handle = BrokerController.brokerhandle_uid_details_map[uid_id]
            return broker_handle
        elif broker == 'jugaadtrader' and broker in BrokerController.instruments_broker_uid:
            uid_id = BrokerController.instruments_broker_uid[broker]
            broker_handle = BrokerController.brokerhandle_uid_details_map[uid_id]
            return broker_handle
            
        return None
    
    @staticmethod
    def get_broker_handle_uid(uid):
        return BrokerController.brokerhandle_uid_details_map[uid]
    
    @staticmethod
    def get_broker_name_uid(uid):
        return BrokerController.uid_uid_details_map[uid]['broker']
    
    @staticmethod
    def get_uid_details_uid(uid):
        return BrokerController.uid_uid_details_map[uid]
    
    @staticmethod
    def save_user_details_to_json(uid):
        all_uid_details = get_users()
        all_uid_details[uid['uid']] = uid
        write_json(all_uid_details, 'ConfigFiles/users.json')
    