# -*- coding: utf-8 -*-
"""Helper Functions"""
import json
import os
import re
import sys
import time
import unicodedata
from .exceptions import ApiError, AppIDError, UnknownPythonError

RATE_ENDPOINT = "https://openexchangerates.org/api/latest.json?show_alternative=1&app_id={}"
CURRENCY_ENDPOINT = "https://openexchangerates.org/api/currencies.json?show_alternative=1"


def _calculate(value, from_currency, to_currency, rates):
    """The Main Calculation of Conversion"""
    from .config import Config
    config = Config()
    return round(value * (rates[to_currency] / rates[from_currency]),
                 config.precision)


def _byteify(loaded_dict):
    if isinstance(loaded_dict, dict):
        return {
            _byteify(key): _byteify(value)
            for key, value in loaded_dict.iteritems()
        }
    if isinstance(loaded_dict, list):
        return [_byteify(element) for element in loaded_dict]
    if isinstance(loaded_dict, unicode):
        return loaded_dict.encode("utf-8")
    return loaded_dict


def is_it_float(query):
    """Check if query is a valid number"""
    try:
        return float(query.replace(",", ""))
    except ValueError:
        return None


def is_it_currency(query):
    """Check if query is a valid currency"""
    currencies = load_currencies()
    query = query.upper()
    if query in currencies:
        return query
    return None


def is_it_symbol(query):
    """Check if query is a valid currency symbol"""
    symbols = load_alias()
    # Full-width to half-width transition
    query = unicodedata.normalize("NFKC", query)
    if sys.version_info.major == 2:
        query = query.encode("utf-8")
    if query in symbols:
        return symbols[query]
    return None


def is_it_something_mixed(query):
    """Check if query is Mixed with value and currency"""

    # Type 1: {number}{currency}
    match_result = re.match(r"^([0-9,]+(\.\d+)?)([A-Z_]+)$", query.upper())
    if match_result:
        value = is_it_float(match_result.groups()[0])
        currency = is_it_currency(match_result.groups()[2])
        if value and currency:
            return (value, currency)

    # Type 2: {currency}{number}
    match_result = re.match(r"^([A-Z_]+)([0-9,]+(\.\d+)?)$", query.upper())
    if match_result:
        value = is_it_float(match_result.groups()[1])
        currency = is_it_currency(match_result.groups()[0])
        if value and currency:
            return (value, currency)

    # Type 3: {symbol}{number}
    match_result = re.match(r"^(.+?)([0-9,]+(\.\d+)?)$",
                            query)  # Use '+?' for non-progressive match
    if match_result:
        value = is_it_float(match_result.groups()[1])
        currency_symbol = is_it_symbol(match_result.groups()[0])
        if value and currency_symbol:
            return (value, currency_symbol)

    return None


def load_currencies(path="currencies.json"):
    """Load currencies, create one if not exists"""
    if not os.path.exists(path):
        return refresh_currencies(path)
    with open(path) as file:
        if sys.version_info.major == 2:
            currencies = _byteify(json.load(file, "utf-8"))
        elif sys.version_info.major == 3:
            currencies = json.load(file)
        else:
            raise UnknownPythonError("Unexpected Python Version")
        return currencies


def refresh_currencies(path="currencies.json"):
    """Fetch the newest currency list"""
    if sys.version_info.major == 2:
        import urllib2
        try:
            response = urllib2.urlopen(CURRENCY_ENDPOINT)
        except urllib2.HTTPError as err:
            response = _byteify(json.load(err, "utf-8"))
            raise ApiError("Unexpected Error", response["description"])
        currencies = _byteify(json.load(response, "utf-8"))
    elif sys.version_info.major == 3:
        from urllib import request, error
        try:
            response = request.urlopen(CURRENCY_ENDPOINT)
        except error.HTTPError as err:
            response = json.load(err)
            raise ApiError("Unexpected Error", response["description"])
        currencies = json.load(response)
    else:
        raise UnknownPythonError("Unexpected Python Version")
    with open(path, "w+") as file:
        json.dump(currencies, file)
    return currencies


def load_alias(path="alias.json"):
    """Load alias, return empty dict if file not found"""
    if not os.path.exists(path):
        return {}
    with open(path) as file:
        if sys.version_info.major == 2:
            alias = _byteify(json.load(file, "utf-8"))
        elif sys.version_info.major == 3:
            alias = json.load(file)
        else:
            raise UnknownPythonError("Unexpected Python Version")
        return alias


def load_symbols(path="symbols.json"):
    """Load symbols, return empty dict if file not found"""
    if not os.path.exists(path):
        return {}
    with open(path) as file:
        if sys.version_info.major == 2:
            symbols = _byteify(json.load(file, "utf-8"))
        elif sys.version_info.major == 3:
            symbols = json.load(file)
        else:
            raise UnknownPythonError("Unexpected Python Version")
        return symbols


def load_rates(path="rates.json"):
    """Load rates, update if not exist or too-old"""
    from .config import Config
    config = Config()
    if not os.path.exists(path):
        return refresh_rates(path)
    with open(path) as file:
        rates = _byteify(json.load(file, "utf-8"))
    last_update = int(time.time() - os.path.getmtime(path))
    if config.expire < last_update:
        return refresh_rates(path)
    # Inject rates file modification datetime
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
        except urllib2.HTTPError as err:
            response = _byteify(json.load(err, "utf-8"))
            if err.code == 401:
                raise AppIDError("Invalid App ID: {}".format(config.app_id),
                                 response["description"])
            elif err.code == 429:
                raise AppIDError("Access Restricted", response["description"])
            else:
                raise ApiError("Unexpected Error", response["description"])
        rates = _byteify(json.load(response, "utf-8"))
    elif sys.version_info.major == 3:
        from urllib import request, error
        try:
            response = request.urlopen(RATE_ENDPOINT.format(config.app_id))
        except error.HTTPError as err:
            response = json.load(err)
            if err.code == 401:
                raise AppIDError("Invalid App ID: {}".format(config.app_id),
                                 response["description"])
            elif err.code == 429:
                raise AppIDError("Access Restricted", response["description"])
            else:
                raise ApiError("Unexpected Error", response["description"])
        rates = json.load(response)
    else:
        raise UnknownPythonError("Unexpected Python Version")
    with open(path, "w+") as file:
        json.dump(rates, file)
    rates["rates"]["last_update"] = "Now"
    return rates["rates"]


def generate_result_items(workflow, value, from_currency, to_currency, rates,
                          icon):
    symbols = load_symbols()
    result = str(_calculate(value, from_currency, to_currency, rates))
    result_symboled = "{}{}".format(symbols[to_currency], result)
    item = workflow.add_item(title="{} {} = {} {}".format(
        value, from_currency, result, to_currency),
                             subtitle="Copy '{}' to clipboard".format(result),
                             icon="flags/{}.png".format(icon),
                             valid=True,
                             arg=result,
                             copytext=result)
    item.add_modifier(
        key="cmd",
        subtitle="Copy '{}' to clipboard".format(result_symboled),
        icon="flags/{}.png".format(icon),
        valid=True,
        arg=result_symboled)
    return item


def generate_list_items(query, raw_items, favorite_filter=None, sort=False):
    currencies = load_currencies()
    items = []
    for abbreviation in raw_items:
        if currencies_filter(query, abbreviation, currencies[abbreviation],
                             favorite_filter):
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
