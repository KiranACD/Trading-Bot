import configparser
from BrokerController.brokercontroller import BrokerController
from Utils import path, filesystem

class User:
    '''
    user will have the broker handle to execute trades.
    Strategies user is registered to.
    Trademanager will create a User object and store them.

    '''

    def __init__(self, uid):
        self.uid = uid
        self.login()

    def get_user_details(self):
        self.broker = self.cfg[self.uid]['broker']
        self.user_id = self.cfg[self.uid]['user_id']
        self.password = self.cfg[self.uid]['password']
        self.totp = self.cfg[self.uid]['totp']

    def login(self):
        BrokerController.handle_broker_login(self.uid)
        self.broker_handle = BrokerController.broker_uid_handle_map[self.uid['uid']]
    
    def test_broker_handle(self):

        if self.broker == 'zerodha':
            try:
                self.broker_handle.profile()
                return True
            except:
                return False
