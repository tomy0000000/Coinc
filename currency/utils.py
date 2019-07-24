"""Helper Functions"""
import json
import os
import sys
import re
import time
from .config import Config

RATE_ENDPOINT = "https://openexchangerates.org/api/latest.json?show_alternative=1&app_id={}"
CURRENCY_ENDPOINT = "https://openexchangerates.org/api/currencies.json?show_alternative=1"

def byteify(loaded_dict):
    if isinstance(loaded_dict, dict):
        return {byteify(key): byteify(value)
                for key, value in loaded_dict.iteritems()}
    if isinstance(loaded_dict, list):
        return [byteify(element) for element in loaded_dict]
    if isinstance(loaded_dict, unicode):
        return loaded_dict.encode("utf-8")
    return loaded_dict

def is_it_currency(query):
    """Check if query is a valid currency"""
    match_result = re.match(r"^[A-Z]{3}$", query.upper())
    if match_result:
        return match_result.string
    return None

def is_it_float(query):
    """Check if query is a valid number"""
    try:
        return float(query)
    except ValueError:
        return None

def is_it_something_mixed(query):
    """Check if query is Mixed with value and currency"""
    match_result = re.match(r"^([0-9]*(\.[0-9]+)?)([A-Z]{3})$", query.upper())
    if match_result:
        value = float(match_result.groups()[0])
        currency = match_result.groups()[2]
        return (value, currency)
    return None

def load_config(path="config.json"):
    """Load config, create one if not exist"""
    if not os.path.exists(path):
        config = Config("XXXXXXXXXX")
        config.save(path)
        return config
    with open(path) as file:
        if sys.version_info.major == 2:
            raw_config = byteify(json.load(file, "utf-8"))
        elif sys.version_info.major == 3:
            raw_config = json.load(file)
        else:
            raise RuntimeError("Unexpected Python Version")
        return Config(**raw_config)

def load_currencies(path="currencies.json"):
    """Load currencies, create one if not exists"""
    if not os.path.exists(path):
        return update_currencies(path)
    with open(path) as file:
        if sys.version_info.major == 2:
            currenies = byteify(json.load(file, "utf-8"))
        elif sys.version_info.major == 3:
            currenies = json.load(file)
        else:
            raise RuntimeError("Unexpected Python Version")
        return currenies

def update_currencies(path):
    if sys.version_info.major == 2:
        import urllib2
        response = urllib2.urlopen(CURRENCY_ENDPOINT)
        currencies = byteify(json.load(response, "utf-8"))
    elif sys.version_info.major == 3:
        import urllib.request
        response = urllib.request.urlopen(CURRENCY_ENDPOINT)
        currencies = json.load(response)
    else:
        raise RuntimeError("Unexpected Python Version")
    with open(path, "w+") as file:
        json.dump(currencies, file)
    return currencies

def load_rates(config, path="rates.json"):
    """Load rates, update if not exist or too-old"""
    if not os.path.exists(path):
        return update_rates(config, path)
    with open(path) as file:
        rates = byteify(json.load(file, "utf-8"))
    # if rates["timestamp"] < int(time.time())-config.expire:
    #     return update_rates(config, path)
    return rates["rates"]

def update_rates(config, path):
    """Update rates with API"""
    if sys.version_info.major == 2:
        import urllib2
        response = urllib2.urlopen(RATE_ENDPOINT.format(config.app_id))
        rates = byteify(json.load(response, "utf-8"))
    elif sys.version_info.major == 3:
        import urllib.request
        response = urllib.request.urlopen(RATE_ENDPOINT.format(config.app_id))
        rates = json.load(response)
    else:
        raise RuntimeError("Unexpected Python Version")
    with open(path, "w+") as file:
        json.dump(rates, file)
    return rates["rates"]

def calculate(value, from_currency, to_currency, config, rates):
    """The Main Calculation of Conversion"""
    return round(
        value * (rates[to_currency] / rates[from_currency]),
        config.precision
    )

def currencies_filter(query, abbreviation, currency, config):
    """Return true if query satisfy certain criterias"""
    if abbreviation in config.currencies:
        return False
    if not query:
        return True
    if abbreviation.startswith(query.upper()):
        return True
    for key_word in currency.split():
        if key_word.lower().startswith(query.lower()):
            return True
    return False
