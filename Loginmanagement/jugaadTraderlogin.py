import os
import logging
from jugaad_trader import Zerodha

class JugaadTradeLogin:

    @staticmethod
    def login(uid):
        os.system(f'jtrader zerodha startsession --option {uid["account_username"]},{uid["account_password"]},{uid["2fa_type"]}:{uid["2fa"]}')
        kite = Zerodha()
        kite.set_access_token()
        try:
            ltp = kite.ltp(['NSE:MARUTI'])
            logging.info(f'LTP of Maruti from Jugaad trader: {str(ltp)}')
        except Exception as e:
            logging.exception('Could not login to jugaad trader')
            return
        return kite
    