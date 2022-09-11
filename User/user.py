from BrokerController.brokercontroller import BrokerController

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
        self.broker = self.uid['broker']
        self.user_id = self.uid['account_username']

    def login(self):
        BrokerController.handle_broker_login(self.uid)
        self.get_user_details()
        self.broker_handle = BrokerController.brokerhandle_uid_details_map[self.uid['uid']]
    
    def test_broker_handle(self):
        if self.broker == 'zerodha':
            try:
                print(self.broker_handle.profile())
                return True
            except:
                return False
        elif self.broker == 'jugaadtrader':
            try:
                print(self.broker_handle.ltp('NSE:MARUTI'))
                return True
            except:
                return False

