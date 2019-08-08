"""Helper Functions"""
import json
import os
import sys
import re
import time

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
    currencies = load_currencies()
    query = query.upper()
    if query in currencies:
        return query
    return None

def is_it_float(query):
    """Check if query is a valid number"""
    try:
        return float(query)
    except ValueError:
        return None

def is_it_something_mixed(query):
    """Check if query is Mixed with value and currency"""
    match_result = re.match(r"^(\d*(\.\d+)?)([A-Z_]*)$", query.upper())
    if match_result:
        value = is_it_float(match_result.groups()[0])
        currency = is_it_currency(match_result.groups()[2])
        if value and currency:
            return (value, currency)
    return None

def load_currencies(path="currencies.json"):
    """Load currencies, create one if not exists"""
    if not os.path.exists(path):
        return refresh_currencies(path)
    with open(path) as file:
        if sys.version_info.major == 2:
            currencies = byteify(json.load(file, "utf-8"))
        elif sys.version_info.major == 3:
            currencies = json.load(file)
        else:
            raise RuntimeError("Unexpected Python Version")
        return currencies

def refresh_currencies(path="currencies.json"):
    """Fetch the newest currency list"""
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

def load_rates(path="rates.json"):
    """Load rates, update if not exist or too-old"""
    from .config import Config
    config = Config()
    if not os.path.exists(path):
        return refresh_rates(path)
    with open(path) as file:
        rates = byteify(json.load(file, "utf-8"))
    last_update = int(time.time() - os.path.getmtime(path))
    if config.expire < last_update:
        return refresh_rates(path)
    # inject rates file modification datetime
    rates["rates"]["last_update"] = "{} seconds ago".format(last_update)
    return rates["rates"]

def refresh_rates(path="rates.json"):
    """Update rates with API"""
    from .config import Config
    config = Config()
    if sys.version_info.major == 2:
        import urllib2
        try:
            response = urllib2.urlopen(RATE_ENDPOINT.format(config.app_id))
        except urllib2.HTTPError:
            raise EnvironmentError(
                "Invalid App ID: {}".format(config.app_id),
                "Fix this in workflow environment variables sheet in Alfred Preferences")
        rates = byteify(json.load(response, "utf-8"))
    elif sys.version_info.major == 3:
        import urllib.request
        from urllib.error import HTTPError
        try:
            response = urllib.request.urlopen(RATE_ENDPOINT.format(config.app_id))
        except HTTPError:
            raise EnvironmentError(
                "Invalid App ID: {}".format(config.app_id),
                "Fix this in workflow environment variables sheet in Alfred Preferences")
        rates = json.load(response)
    else:
        raise RuntimeError("Unexpected Python Version")
    with open(path, "w+") as file:
        json.dump(rates, file)
    rates["rates"]["last_update"] = "Now"
    return rates["rates"]

def calculate(value, from_currency, to_currency, rates):
    """The Main Calculation of Conversion"""
    from .config import Config
    config = Config()
    return round(
        value * (rates[to_currency] / rates[from_currency]), config.precision
    )

def generate_items(query, raw_items, favorite_filter=None, sort=False):
    currencies = load_currencies()
    items = []
    for abbreviation in raw_items:
        if currencies_filter(query, abbreviation, currencies[abbreviation], favorite_filter):
            items.append({
                "title": currencies[abbreviation],
                "subtitle": abbreviation,
                "icon": "flags/{}.png".format(abbreviation),
                "valid": True,
                "arg": abbreviation
            })
    if sort:
        items = sorted(items, key=lambda item: item["subtitle"])
    return items

def currencies_filter(query, abbreviation, currency, favorite=None):
    """Return true if query satisfy certain criterias"""
    favorite = favorite or []
    if abbreviation in favorite:
        return False
    if not query:
        return True
    if abbreviation.startswith(query.upper()):
        return True
    for key_word in currency.split():
        if key_word.lower().startswith(query.lower()):
            return True
    return False
