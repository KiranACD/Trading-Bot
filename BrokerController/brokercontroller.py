import logging
from Loginmanagement.zerodhalogin import ZerodhaLogin
from Ordermanagement.zerodhaordermanager import ZerodhaOrderManager
# from Ordermanagement.

class BrokerController:

    brokers = []
    broker_uid_details_map = {}
    broker_ticker_uid = {}
    instruments_broker_handle = {}
    uid_order_manager_map = {}

    @staticmethod
    def handle_broker_login(uid):
        if uid['broker'] == 'zerodha':
            uid = ZerodhaLogin.login(uid)
            logging.info(f'Logged into {uid["name"]} with user id {uid["user_id"]}')
            BrokerController.broker_uid_details_map[uid['uid']] = uid
            if uid['ticker'] and 'zerodha' not in BrokerController.broker_ticker_uid:
                BrokerController.broker_ticker_uid['zerodha'] = uid['uid']
            if 'zerodha' not in BrokerController.instruments_broker_handle:
                BrokerController.instruments_broker_handle['zerodha'] = uid['uid']
            if 'zerodha' not in BrokerController.brokers:
                BrokerController.brokers.append('zerodha')
    
    @staticmethod
    def set_broker_handle(uid):
        if uid['broker'] == 'zerodha':
            uid = ZerodhaLogin.set_broker_handle(uid)
            BrokerController.broker_uid_name_map[uid['uid']] = uid['name']
            BrokerController.broker_uid_name_map[uid['uid']] = uid['broker_handle']
            BrokerController.broker_uid_name_map[uid['uid']] = uid['access_token']
    
    @staticmethod
    def get_ticker_accesscode(broker):
        if broker == 'zerodha' and broker in BrokerController.broker_ticker_uid:
            uid_id = BrokerController.broker_ticker_uid[broker]
            uid_details = BrokerController.broker_uid_details_map[uid_id]
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
    def get_instrument_handle(broker):
        if broker == 'zerodha' and broker in BrokerController.instruments_broker_handle:
            uid_id = BrokerController.broker_ticker_uid[broker]
            uid_details = BrokerController.broker_uid_details_map[uid_id]
            broker_handle = uid_details['broker_handle']
            return broker_handle
        return None
    
    @staticmethod
    def get_order_manager(uid):
        if uid in BrokerController.uid_order_manager_map:
            return BrokerController.uid_order_manager_map[uid]
        uid_details = BrokerController.broker_uid_details_map[uid]
        if uid_details['name'] == 'zerodha':
            order_manager = ZerodhaOrderManager(uid)
            BrokerController.uid_order_manager_map[uid] = order_manager
            return order_manager
    
    @staticmethod
    def get_broker_handle_uid(uid):
        return BrokerController.broker_uid_details_map[uid]['broker_handle']
    
    @staticmethod
    def get_broker_name_uid(uid):
        return BrokerController.broker_uid_details_map[uid]['broker']
    