from email import header
from webbrowser import get
import requests
import json
import urllib.parse as urlparse
import datetime
from fyers_api import fyersModel, accessToken
from Config.config import get_server_config

class FyersLogin:

    @staticmethod
    def login(cfg):
        log_file_path = get_server_config()['logfiledir']
        app_id = cfg['app_id']
        secret_id = cfg['secret_id']
        redirect_url = cfg['redirect_url']
        response_type = cfg['response_type']
        grant_type = cfg['grant_type']
        client_id = cfg['account_username']
        password = cfg['account_password']
        two_fa = cfg['two_fa']
        app_id_post = app_id.split('-')[0]
        login_url = cfg['login_url']
        verify_url = cfg['verify_url']
        token_url = cfg['token_url']


        app_session = accessToken.SessionModel(client_id=app_id, secret_key=secret_id, 
                                               redirect_uri=redirect_url, response_type=response_type,
                                               grant_type=grant_type)
        
        response_url = app_session.generate_authcode()
        headers = {"accept":"*/*",
                   "accept-language":"en-IN,en-US;q=0.9,en;q=0.8",
                   "content-type":"application/json; charset=UTF-8",
                   "sec-fetch-dest":"empty",
                   "sec-fetch-mode":"cors",
                   "sec-fetch-site":"same-origin",
                   "referrer":response_url}
        
        input1 = {'fy_id':client_id, "password": password, "app_id":'2', "imei":"", "recaptcha_token":""}
        session = requests.Session()
        result = session.post(login_url, headers=headers, json=input1)
        var = json.loads(result.content)

        input2 = {'identifier':'3602', 'identity_type':'pin', 'recaptcha_token':"", 'request_key':var['request_key']}
        result = session.post(verify_url, headers=headers, json=input2)

        var1 = json.loads(result.content)

        main_input = {"fyers_id": client_id, "password": password, "pan_dob": two_fa, "app_id": app_id_post,
                      "redirect_uri": redirect_url, "appType":"100", "code_challenge":"", "state":"private",
                      "scope":"", "nonce":"private", "response_type":"code", "create_cookie":True}

        headers = {"accept":"*/*",
                   "accept-language":"en-IN,en-US;q=0.9,en;q=0.8",
                   "content-type":"application/json; charset=UTF-8",
                   "sec-fetch-dest":"empty",
                   "sec-fetch-mode":"cors",
                   "sec-fetch-site":"same-origin",
                   "referrer":response_url,
                   "Authorization":"Bearer " + var1['data']['access_token']}
        
        result = session.post(token_url, headers=headers, json=main_input, allow_redirects=True)
        var = json.loads(result.content)
        url = var['Url']

        parsed = urlparse.urlparse(url)
        parsedlist = urlparse.parse_qs(parsed.query)['auth_code']
        auth_code = parsedlist[0]
        app_session.set_token(auth_code)
        response = app_session.generate_token()
        access_token = response['access_token']
        fyers = fyersModel.FyersModel(client_id=app_id, token=access_token, log_path=log_file_path)

        cfg['access_token_date'] = str(datetime.datetime.today().date())
        cfg['access_token'] = access_token

        return fyers
    
    @staticmethod
    def set_broker_handle(uid):

        app_id = uid['app_id']
        access_token = uid['access_token']
        log_file_path = get_server_config()['logfiledir']
        fyers = fyersModel.FyersModel(client_id=app_id, token=access_token, log_path=log_file_path)
        
        return fyers
