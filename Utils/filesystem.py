"""
save and load the config file
"""
import json
import pickle

def write_config(filename, config):
    """
    filename should have .ini extension  passed as arg
    """
    if not filename.endswith('.ini'):
        raise NameError("Filename should have .ini as extension.")
    with open(filename, "w") as configfile:
        config.write(configfile)

def write_json(file, filename):
    """
    filename should have .json extension passed as arg
    """
    if ".json" not in filename:
        raise NameError("Filename should have .json as extension.")
    with open(filename, "w") as json_file:
        json.dump(file, json_file)


def read_json(filename):
    """
    filename should have .json extension passed as arg
    """
    if ".json" not in filename:
        raise NameError("Filename should have .json as extension.")
    with open(filename) as json_file:
        return json.load(json_file)

def write_pickle(file, filename):
    """
    filename should have .pickle extension passed as arg
    """
    if ".pickle" not in filename:
        raise NameError("Filename should have .pickle as extension.")
    with open(filename, "wb") as handle:
        pickle.dump(file, handle, protocol=pickle.HIGHEST_PROTOCOL)


def read_pickle(filename):
    """
    filename should have .pickle extension passed as arg
    """
    if ".pickle" not in filename:
        raise NameError("Filename should have .pickle as extension.")
    with open(filename, "rb") as handle:
        return pickle.load(handle)