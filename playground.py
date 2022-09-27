import logging
# import datetime
import threading
import time
# from User.user import User
# from User.userdecoder import UserDecoder
# from BrokerController.brokercontroller import BrokerController
# from Instruments.instruments import Instruments
# 
# from Ticker.zerodhaquoteticker import ZerodhaQuoteTicker
from Strategies.niftyshortstraddle import NiftyShortStraddle
from Strategies.niftyshortstraddleISL920 import NiftyShortStraddleISL920
from Strategies.bankniftyshortstraddle import BankniftyShortStraddle
from Strategies.bankniftystraddleadjust import BankniftyStraddleAdjust
from Trademanagement.trademanager import TradeManager
# from Ticker.zerodhaquoteticker import ZerodhaQuoteTicker
# from Ordermanagement.zerodhaordermanager import ZerodhaOrderManager
from Config.config import get_users, get_server_config

# path1 = 'ConfigFiles/'
# path2 = 'trades'

# print(os.path.join(path1, path2))

# uid_users = get_users()
# print(uid_users)

def init_logging(filepath):
    format = '%(asctime)s: %(message)s'
    logging.basicConfig(filename=filepath, format=format, level = logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

server_config = get_server_config()
log_file_dir = server_config['logfiledir']

init_logging(log_file_dir + '/app.log')

# NiftyShortStraddle.init_service()
# NiftyShortStraddleISL920.get_instance().run()

logging.info('Starting Algo...')
tm = threading.Thread(target=TradeManager.run)
tm.start()

time.sleep(5)
NiftyShortStraddle.init_service()
BankniftyShortStraddle.init_service()

threading.Thread(target=NiftyShortStraddleISL920.get_instance().run).start()
threading.Thread(target=BankniftyStraddleAdjust.get_instance().run).start()


# users_uid = get_users(UserDecoder)
# for uid in users_uid:
#     user_obj = User(users_uid[uid])
#     # Test each user object to check if login is a success. Make a profile call.
#     if user_obj.test_broker_handle():
#         continue
#     else:
#         logging.info(f'{user_obj.uid} not logged in.')
#         continue

# for broker in BrokerController.brokers:
#     Instruments.fetch_instruments(broker)

# print(Instruments.instruments_list.keys())
# NiftyShortStraddle.init_service()

# ticker = ZerodhaQuoteTicker().get_instance()
# ticker.start_ticker()
# ticker.register_symbols(NiftyShortStraddle.symbol_dict_list, NiftyShortStraddle.config['uid'])

# now = datetime.datetime.now()
# while (datetime.datetime.now() - now).seconds < 100:
#     continue
# ticker.stop_ticker()

