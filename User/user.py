import logging
from BrokerController.brokercontroller import BrokerController 

class User:
    '''
    user will have the broker handle to execute trades.
    Strategies user is registered to.
    Trademanager will create a User object and store them.

    '''

    def __init__(self, uid):
        self.uid_details = uid
        self.login()

    def get_user_details(self):
        self.uid = self.uid_details['uid']
        self.broker = self.uid_details['broker']
        self.user_id = self.uid_details['account_username']
        self.paper_trade = self.uid_details['paper_trade']
        self.subscribed_strategies = self.uid_details['subscribed_strategies'].split(',')
        self.subscribed_strategies = [strategy for strategy in self.subscribed_strategies if strategy]
        self.strategy_capital_allocation = self.uid_details['strategy_capital_allocation'].split(',')
        self.strategy_capital_allocation = [cap_alloc for cap_alloc in self.strategy_capital_allocation if cap_alloc]
        self.strategy_capital_allocation = list(map(int, self.strategy_capital_allocation))
        self.strategy_capital_map = {}
        for strategy, cap_allocation in zip(self.subscribed_strategies, self.strategy_capital_allocation):
            self.strategy_capital_map[strategy] = cap_allocation
        self.capital = self.uid_details['capital']


    def login(self):
        BrokerController.handle_broker_login(self.uid_details)
        self.get_user_details()
        self.broker_handle = BrokerController.brokerhandle_uid_details_map[self.uid_details['uid']]

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
        elif self.broker == 'fyers':
            try:
                print(self.broker_handle.get_profile())
                return True
            except:
                return False
        

