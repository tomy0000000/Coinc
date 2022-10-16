# -*- coding: utf-8 -*-
"""Helper Functions"""
import json
import os
import plistlib
import re
import time
import unicodedata
from decimal import Decimal
from urllib import error, request

from .exceptions import ApiError, AppIDError

INFO_PLIST_PATH = "info.plist"
OLD_BUNDLE_ID = "tech.tomy.coon"
NEW_BUNDLE_ID = "tech.tomy.coinc"
WORKFLOW_DATA_PATH = "~/Library/Application Support/Alfred/Workflow Data"
RATE_ENDPOINT = (
    "https://openexchangerates.org/api/latest.json?show_alternative=1&app_id={}"
)
CURRENCY_ENDPOINT = (
    "https://openexchangerates.org/api/currencies.json?show_alternative=1"
)


def manual_update_patch(workflow):
    """manual update metadatas for v1.3.0 name change

    Update include two section, change Bundle ID in info.plist to a new one,
    and rename the old data directory into new one

    Arguments:
        workflow {workflow.Workflow3} -- The workflow object

    Returns:
        bool -- Whether any modification got invoked
    """
    updated = False
    # Fix Bundle ID
    if workflow.bundleid.encode("utf-8") == OLD_BUNDLE_ID:
        with open(INFO_PLIST_PATH, "rw") as file:
            info = plistlib.load(file)
            info["bundleid"] = NEW_BUNDLE_ID
            plistlib.dump(info, INFO_PLIST_PATH)
        workflow.logger.info("Bundle ID modified")
        updated = True

    # Move Data Directory
    old_path = os.path.expanduser(os.path.join(WORKFLOW_DATA_PATH, OLD_BUNDLE_ID))
    if os.path.exists(old_path):
        new_path = os.path.expanduser(os.path.join(WORKFLOW_DATA_PATH, NEW_BUNDLE_ID))
        os.rename(old_path, new_path)
        workflow.logger.info("Data Directory moved")
        updated = True
    return updated


def init_workflow(workflow):
    """Run operation to get workflow ready

    Inject config into Workflow

    Arguments:
        workflow {workflow.Workflow3} -- The workflow object

    Returns:
        workflow -- the passed in workflow object
    """
    from .config import Config

    workflow.config = Config()
    workflow.logger.info(
        f"Locale: {'(System)' if not workflow.config.locale else workflow.config.locale}"
    )
    return workflow


def _calculate(value, from_currency, to_currency, rates, precision):
    """The Main Calculation of Conversion

    Arguments:
        value {float} -- amount of from_currency to be convert
        from_currency {str} -- currency code of value
        to_currency {str} -- currency code to be convert
        rates {dict} -- rates used to perform conversion
        precision {int} -- precision point to be round

    Returns:
        float -- The result of the conversion
    """
    return round(
        Decimal(value) * (Decimal(rates[to_currency]) / Decimal(rates[from_currency])),
        precision,
    )


def is_it_float(query):
    """Check if query is a valid number

    Arguments:
        query {str} -- Input query string

    Returns:
        float -- Parsed float
        None -- if query failed to be parsed
    """
    try:
        return float(query.replace(",", ""))
    except ValueError:
        return None


def is_it_currency(query):
    """Check if query is a valid currency

    Arguments:
        query {str} -- Input query string

    Returns:
        str -- Normalized currency code
        None -- if query failed to be parsed
    """
    currencies = load_currencies()
    query = query.upper()
    if query in currencies:
        return query
    return None


def is_it_symbol(query):
    """Check if query is a valid currency symbol

    Arguments:
        query {str} -- Input query string

    Returns:
        str -- Normalized currency code
        None -- if query failed to be parsed
    """
    symbols = load_alias()
    # Full-width to half-width transition
    query = unicodedata.normalize("NFKC", query).upper()
    if query in symbols:
        return symbols[query]
    return None


def is_it_something_mixed(query):
    """Check if query is Mixed with value and currency

    [description]

    Arguments:
        query {str} -- Input query string

    Returns:
        tuple -- tuple with type (<float>, <str>) contain parsed float and
                 normalized currency code, respectively
        None -- if query failed to be parsed
    """

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
    match_result = re.match(
        r"^(.+?)([0-9,]+(\.\d+)?)$", query
    )  # Use '+?' for non-progressive match
    if match_result:
        value = is_it_float(match_result.groups()[1])
        currency_symbol = is_it_symbol(match_result.groups()[0])
        if value and currency_symbol:
            return (value, currency_symbol)

    return None


def load_currencies(path="currencies.json"):
    """Load currency list, create one if not exists

    Keyword Arguments:
        path {str} -- path or filename of Currencies JSON
                      (default: {"currencies.json"})

    Returns:
        dict -- loaded dictionary of currency list
    """
    if not os.path.exists(path):
        return refresh_currencies(path)
    last_update = int(time.time() - os.path.getmtime(path))
    # Update currencies list if too old (30 days)
    if 2592000 < last_update:
        return refresh_currencies(path)
    with open(path) as file:
        currencies = json.load(file)
    return currencies


def refresh_currencies(path="currencies.json"):
    """Fetch and save the newest currency list

    Keyword Arguments:
        path {str} -- path or filename of Currencies JSON to be saved
                      (default: {"currencies.json"})

    Returns:
        dict -- fetched dictionary of currency list

    Raises:
        ApiError -- Raised when API is unreachable or return bad response
    """
    try:
        response = request.urlopen(CURRENCY_ENDPOINT)
    except error.HTTPError as err:
        response = json.load(err)
        raise ApiError("Unexpected Error", response["description"])
    currencies = json.load(response)
    with open(path, "w+") as file:
        json.dump(currencies, file)
    return currencies


def load_rates(config, path="rates.json"):
    """Load rates, update if not exist or too-old

    Arguments:
        config {currency.config} -- Config object

    Keyword Arguments:
        path {str} -- path or filename of Rates JSON (default: {"rates.json"})

    Returns:
        dict -- loaded dictionary of rates
    """
    if not os.path.exists(path):
        return refresh_rates(config, path)
    with open(path) as file:
        rates = json.load(file)
    last_update = int(time.time() - os.path.getmtime(path))
    if config.expire < last_update:
        return refresh_rates(config, path)
    # Inject rates file modification datetime
    rates["rates"]["last_update"] = f"{last_update} seconds ago"
    return rates["rates"]


def refresh_rates(config, path="rates.json"):
    """Fetch and save the newest rates

    Arguments:
        config {currency.config} -- Config object

    Keyword Arguments:
        path {str} -- path or filename of Rates JSON to be saved
                      (default: {"rates.json"})

    Returns:
        dict -- fetched dictionary of rates

    Raises:
        AppIDError -- Raised when App ID can not be used
        ApiError -- Raised when API is unreachable or return bad response
    """

    try:
        response = request.urlopen(RATE_ENDPOINT.format(config.app_id))
    except error.HTTPError as err:
        response = json.load(err)
        if err.code == 401:
            raise AppIDError(
                f"Invalid App ID: {config.app_id}", response["description"]
            )
        elif err.code == 429:
            raise AppIDError("Access Restricted", response["description"])
        else:
            raise ApiError("Unexpected Error", response["description"])
    rates = json.load(response)
    with open(path, "w+") as file:
        json.dump(rates, file)
    rates["rates"]["last_update"] = "Now"
    return rates["rates"]


def load_alias(path="alias.json"):
    """Load alias, return empty dict if file not found

    Keyword Arguments:
        path {str} -- path or filename of Alias JSON (default: {"alias.json"})

    Returns:
        dict -- loaded dictionary of alias
    """
    if not os.path.exists(path):
        return {}
    with open(path) as file:
        alias = json.load(file)
    return alias


def load_symbols(path="symbols.json"):
    """Load symbols, return empty dict if file not found

    Keyword Arguments:
        path {str} -- path or filename of Symbols JSON
                      (default: {"symbols.json"})

    Returns:
        dict -- loaded dictionary of symbols
    """
    if not os.path.exists(path):
        return {}
    with open(path) as file:
        symbols = json.load(file)
    return symbols


def generate_result_item(workflow, value, from_currency, to_currency, rates, icon):
    """Calculate conversion result and append item to workflow

    Arguments:
        workflow {workflow.Workflow3} -- The workflow object
        value {float} -- amount of from_currency to be convert
        from_currency {str} -- currency code of value
        to_currency {str} -- currency code to be convert
        rates {dict} -- rates used to perform conversion
        icon {str} -- currency code of icon to be display for workflow item

    Returns:
        workflow.workflow3.Item3 -- Item3 object generated
    """
    symbols = load_symbols()
    result = _calculate(
        value, from_currency, to_currency, rates, workflow.config.precision
    )
    result_symboled = f"{symbols[to_currency]}{result:n}"
    item = workflow.add_item(
        title=f"{value:n} {from_currency} = {result:n} {to_currency}",
        subtitle=f"Copy '{result:n}' to clipboard",
        icon=f"flags/{icon}.png",
        valid=True,
        arg=f"{result:n}",
        copytext=f"{result:n}",
    )
    item.add_modifier(
        key="alt",
        subtitle=f"Copy '{result_symboled}' to clipboard",
        icon=f"flags/{icon}.png",
        valid=True,
        arg=result_symboled,
    )
    return item


def generate_list_items(query, currency_codes, favorite_filter=None, sort=False):
    """Generate items from currency codes that can be add to workflow

    Arguments:
        query {str} -- Input query string
        currency_codes {list} -- list of currency code that are used to
                                 generate items

    Keyword Arguments:
        favorite_filter {list} -- list of favorites currency code
                                  (default: {None})
        sort {bool} -- should items be sort (default: {False})

    Returns:
        list -- list of items generate from currency_codes that can be add to
                workflow
    """
    currencies = load_currencies()
    items = []
    for code in currency_codes:
        if currencies_filter(query, code, currencies[code], favorite_filter):
            items.append(
                {
                    "title": currencies[code],
                    "subtitle": code,
                    "icon": f"flags/{code}.png",
                    "valid": True,
                    "arg": code,
                }
            )
    if sort:
        items = sorted(items, key=lambda item: item["subtitle"])
    return items


def currencies_filter(query, code, currency_name, favorites=None):
    """Determine whether query matched with the code or currency name

    For query to match, it must not be a item in favorites
    (if favorites is provided), and be one of the following:
    * Empty query
    * Matching code from start (case insensitive)
    * Matching one of the word in currency_name from start (case insensitive)

    Arguments:
        query {str} -- Input query string
        code {str} -- Currency code
        currency_name {str} -- Full name of currency

    Keyword Arguments:
        favorites {list} -- list of favorites currency code (default: {None})

    Returns:
        bool -- True if matched else False
    """
    favorites = favorites or []
    if code in favorites:
        return False
    if not query:
        return True
    if code.startswith(query.upper()):
        return True
    for key_word in currency_name.split():
        if key_word.lower().startswith(query.lower()):
            return True
    return False
