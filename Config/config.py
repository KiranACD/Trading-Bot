import json
import pickle
import os

def get_holidays():
    with open('ConfigFiles/holidays.json', 'r') as holidays:
        holidays_data = json.load(holidays)
        return holidays_data

def get_users():
    with open('ConfigFiles/users.json', 'r') as users:
        user_uid = json.load(users)
        return users

def get_server_config():
    with open('ConfigFiles/server.json', 'r') as server:
        json_server_data = json.load(server)
        return json_server_data

def get_login_state():
    with open('ConfigFiles/login_state.json', 'r') as login_state:
        login_state_data = json.load(login_state)
        return login_state_data

def get_ticker_user():
    with open('ConfigFiles/ticker_user.json', 'r') as ticker_user:
        ticker_user_data = json.load(ticker_user)
        return ticker_user_data

def get_instruments_json():
    with open('ConfigFiles/instruments_config.json') as inst:
        instruments_json = json.load(inst)
    return instruments_json

def read_json(filename):
    """
    filename should have .json extension passed as arg
    """
    if not filename.endswith(".json"):
        raise NameError("Filename should have .json as extension.")
    with open(filename) as json_file:
        return json.load(json_file)

def write_json(file, filename, indent = 2, cls = None):
    """
    filename should have .json extension passed as arg
    """
    if not filename.endswith(".json"):
        raise NameError("Filename should have .json as extension.")
    with open(filename, "w") as json_file:
        json_file.seek(0)
        if cls is None:
            json.dump(file, json_file)
        else:
            json.dump(file, json_file, indent=indent, cls=cls)
        json_file.truncate()

def write_pickle(file, filename):
    """
    filename should have .pickle extension passed as arg
    """
    if not filename.endswith(".pickle"):
        raise NameError("Filename should have .pickle as extension.")
    with open(filename, "wb") as handle:
        pickle.dump(file, handle, protocol=pickle.HIGHEST_PROTOCOL)


def read_pickle(filename):
    """
    filename should have .pickle extension passed as arg
    """
    if not filename.endswith(".pickle"):
        raise NameError("Filename should have .pickle as extension.")
    with open(filename, "rb") as handle:
        return pickle.load(handle)