"""Helper Functions"""
import json
import locale
import os
import plistlib
import re
import time
import unicodedata
from decimal import Decimal
from typing import Union
from urllib import error, request

from workflow import Workflow3
from workflow.workflow3 import Item3

from .alfred import persisted_data
from .config import Config
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


def manual_update_patch(workflow: Workflow3) -> bool:
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
        with open(INFO_PLIST_PATH, "rwb") as file:
            info = plistlib.load(file)
            info["bundleid"] = NEW_BUNDLE_ID
            plistlib.dump(info, file)
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


def init_workflow(workflow: Workflow3) -> Workflow3:
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


def _calculate(
    value: float, from_currency: str, to_currency: str, rates: dict, precision: int
) -> Decimal:
    """The Main Calculation of Conversion

    Arguments:
        value {float} -- amount of from_currency to be convert
        from_currency {str} -- currency code of value
        to_currency {str} -- currency code to be convert
        rates {dict} -- rates used to perform conversion
        precision {int} -- precision point to be round

    Returns:
        Decimal -- The result of the conversion
    """
    return round(
        Decimal(value) * (Decimal(rates[to_currency]) / Decimal(rates[from_currency])),
        precision,
    )


def _format(value: Union[Decimal, float], precision) -> str:
    """Format the result of conversion

    Arguments:
        value {Decimal} -- The result of conversion
        precision {int} -- precision point to be round

    Returns:
        str -- The formatted result
    """
    return locale.format_string(f"%.{precision}f", value, grouping=True, monetary=True)


def is_it_float(query: str) -> Union[float, None]:
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


def is_it_currency(config: Config, query: str) -> Union[str, None]:
    """Check if query is a valid currency

    Arguments:
        query {str} -- Input query string

    Returns:
        str -- Normalized currency code
        None -- if query failed to be parsed
    """
    rates = load_rates(config)
    query = query.upper()
    if query in rates:
        return query
    return None


def is_it_alias(query: str) -> Union[str, None]:
    """Check if query is a valid currency symbol

    Arguments:
        query {str} -- Input query string

    Returns:
        str -- Normalized currency code
        None -- if query failed to be parsed
    """
    aliases = persisted_data("alias")
    # Full-width to half-width transition
    query = unicodedata.normalize("NFKC", query).upper()
    if query in aliases:
        return aliases[query]
    return None


def is_it_something_mixed(config: Config, query: str) -> Union[tuple[float, str], None]:
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
        currency = is_it_currency(config, match_result.groups()[2])
        if value and currency:
            return (value, currency)

    # Type 2: {currency}{number}
    match_result = re.match(r"^([A-Z_]+)([0-9,]+(\.\d+)?)$", query.upper())
    if match_result:
        value = is_it_float(match_result.groups()[1])
        currency = is_it_currency(config, match_result.groups()[0])
        if value and currency:
            return (value, currency)

    # Type 3: {alias}{number}
    match_result = re.match(
        r"^(.+?)([0-9,]+(\.\d+)?)$", query
    )  # Use '+?' for non-progressive match
    if match_result:
        value = is_it_float(match_result.groups()[1])
        currency_alias = is_it_alias(match_result.groups()[0])
        if value and currency_alias:
            return (value, currency_alias)

    # Type 4: {number}{alias}
    match_result = re.match(
        r"^([0-9,]+(\.\d+)?)(.*?)$", query
    )  # Use '+?' for non-progressive match
    if match_result:
        value = is_it_float(match_result.groups()[0])
        currency_alias = is_it_alias(match_result.groups()[2])
        if value and currency_alias:
            return (value, currency_alias)

    # If nothing matched
    return None


def load_currencies(path: Union[str, os.PathLike] = "currencies.json") -> dict:
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


def refresh_currencies(path: Union[str, os.PathLike] = "currencies.json") -> dict:
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


def load_rates(config: Config, path: Union[str, os.PathLike] = "rates.json") -> dict:
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


def refresh_rates(config: Config, path: Union[str, os.PathLike] = "rates.json") -> dict:
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


def add_alias(alias: str, currency: str) -> None:
    """Save new alias

    Arguments:
        alias {str} -- new alias
        currency {str} -- currency code
    """
    aliases = persisted_data("alias")
    aliases[alias] = currency
    persisted_data("alias", aliases)


def remove_alias(alias: str) -> None:
    """Remove alias

    Arguments:
        alias {str} -- alias to be removed
    """
    aliases = persisted_data("alias")
    aliases.pop(alias)
    persisted_data("alias", aliases)


def load_symbols(path: Union[str, os.PathLike] = "symbols.json") -> dict:
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


def generate_result_item(
    workflow: Workflow3,
    value: float,
    from_currency: str,
    to_currency: str,
    rates: dict,
    icon: str,
) -> Item3:
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
    value_formatted = _format(value, workflow.config.precision)
    result_formatted = _format(result, workflow.config.precision)
    result_symboled = f"{symbols[to_currency]}{result_formatted}"
    item = workflow.add_item(
        title=f"{value_formatted} {from_currency} = {result_formatted} {to_currency}",
        subtitle=f"Copy '{result_formatted}' to clipboard",
        icon=f"flags/{icon}.png",
        valid=True,
        arg=f"{result_formatted}",
        copytext=f"{result_formatted}",
    )
    item.add_modifier(
        key="alt",
        subtitle=f"Copy '{result_symboled}' to clipboard",
        icon=f"flags/{icon}.png",
        valid=True,
        arg=result_symboled,
    )
    return item


def generate_list_items(
    query: str,
    currency_codes: list,
    filter: Union[list, None] = None,
    sort: bool = False,
) -> list:
    """Generate items from currency codes that can be add to workflow

    Arguments:
        query {str} -- Input query string
        currency_codes {list} -- list of currency code that are used to
                                 generate items

    Keyword Arguments:
        filter {list} -- list of favorites currency code
                         (default: {None})
        sort {bool} -- should items be sort (default: {False})

    Returns:
        list -- list of items generate from currency_codes that can be add to
                workflow
    """
    currencies = load_currencies()
    items = []
    for code in currency_codes:
        if currencies_filter(query, code, currencies[code], filter):
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


def currencies_filter(
    query: str, code: str, currency_name: str, filter: Union[list, None] = None
) -> bool:
    """Determine whether query matched with the code or currency name

    For query to match, it must not be a item in filter
    (if filter is provided), and be one of the following:
    * Empty query
    * Matching code from start (case insensitive)
    * Matching one of the word in currency_name from start (case insensitive)

    Arguments:
        query {str} -- Input query string
        code {str} -- Currency code
        currency_name {str} -- Full name of currency

    Keyword Arguments:
        filter {list} -- list of filter currency code (default: {None})

    Returns:
        bool -- True if matched else False
    """
    filter = filter or []
    if code in filter:
        return False
    if not query:
        return True
    if code.startswith(query.upper()):
        return True
    for key_word in currency_name.split():
        if key_word.lower().startswith(query.lower()):
            return True
    return False
