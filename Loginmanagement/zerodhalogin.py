import pyotp
import requests
import datetime
import urllib.parse as urlparse
from kiteconnect import KiteConnect
class ZerodhaLogin:

    @staticmethod
    def login(cfg):
        request_token = ''

        api_key = cfg['api_key']
        api_secret = cfg['api_secret']
        account_username = cfg['account_username']
        account_password = cfg['account_password']
        totp = cfg['totp']
        auth_key = pyotp.TOTP(totp)
        
        # Session for login
        session = requests.Session()
        
        url = cfg['url'].format(api_key)
        response = session.get(url)
        response_url = response.url

        login_url = cfg['login_url']
        payload = {'user_id':account_username, 'password':account_password}
        response = session.post(login_url, data=payload)

        twofa_url = cfg['twofa_url']
        twofa_payload = {"user_id":account_username, "request_id":response.json()['data']['request_id'],
                            "twofa_value":auth_key.now(), "skip_session":"true"}
        response = session.post(twofa_url, twofa_payload)

        headers = {"Cookie":"__cfduid={}; kf_session={}; user_id={}; public_token={}; enctoken={}".
                    format(session.cookies.get(name='__cfduid'), session.cookies.get(name='kf_session'),
                           account_username, session.cookies.get(name='public_token'),
                           response.headers.get('Set-Cookie').split('enctoken=')[1].split(';')[0])}
        
        try:
            response = session.get('{}&skip_session=true'.format(response_url), headers=headers)
        except Exception as e:
            print(e)
        
        parsed = urlparse.urlparse(response.url)
        request_token = urlparse.parse_qs(parsed.query)['request_token'][0]

        kite = KiteConnect(api_key=api_key)
        access_token = kite.generate_session(request_token=request_token, api_secret=api_secret)['access_token']
        kite.set_access_token(access_token)

        cfg['access_token_date'] = str(datetime.datetime.today().date())
        cfg['access_token'] = access_token

        # cfg['broker_handle'] = kite

        # return cfg
        return kite
    
    def set_broker_handle(uid):

        api_key = uid['api_key']
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(uid['access_token'])
        # uid['broker_handle'] = kite
        # return uid
        return kite