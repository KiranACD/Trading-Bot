import logging
import threading
import time
from Strategies.niftyshortstraddle import NiftyShortStraddle
from Strategies.niftyshortstraddleISL920 import NiftyShortStraddleISL920
from Strategies.niftyshortstraddleISL920rentry1330 import NiftyShortStraddleISL920rentry1330
from Strategies.bankniftyshortstraddle import BankniftyShortStraddle
from Strategies.bankniftystraddleadjust import BankniftyStraddleAdjust
from Trademanagement.trademanager import TradeManager
from Config.config import get_server_config

def init_logging(filepath):
    format = '%(asctime)s: %(message)s'
    logging.basicConfig(filename=filepath, format=format, level = logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

server_config = get_server_config()
log_file_dir = server_config['logfiledir']

init_logging(log_file_dir + '/app.log')

logging.info('Starting Algo...')
tm = threading.Thread(target=TradeManager.run)
tm.start()

print('Sleeping for 5 seconds while users login and feed is initialized')
time.sleep(5)

NiftyShortStraddle.init_service()
BankniftyShortStraddle.init_service()

while len(TradeManager.users) == 0:
    print('Users not yet available.')
    time.sleep(5)
    continue

print('Starting strategies')
# threading.Thread(target=NiftyShortStraddleISL920.get_instance().run).start()
# threading.Thread(target=BankniftyStraddleAdjust.get_instance().run).start()
threading.Thread(target=NiftyShortStraddleISL920rentry1330.get_instance().run).start()