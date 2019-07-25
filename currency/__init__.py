"""Function to be called by workflow"""
from .query import Query
from .utils import load_config, load_rates, load_currencies, calculate, currencies_filter
from .workflow import ICON_WARNING

__all__ = [
    "load_all_currencies",
    "load_favorite_currencies",
    "convert",
    "add",
    "remove",
    "move",
    "base",
    "help_me"
]

def load_all_currencies(workflow):
    """Load all available currencies"""
    settings = workflow.settings
    config = load_config()
    currencies = load_currencies()
    if len(workflow.args) > 2:
        raise ValueError("One Currency at a time, please")
    args = workflow.args[1:]
    query = "" if not args else str(args[0]).upper()
    # TODO: Try implement this after Python 3 Support
    # abb_filtered = workflow.filter(query, currencies.items(), key=lambda item: item[0])
    # cur_filtered = workflow.filter(query, currencies.items(), key=lambda item: item[1])
    # items = list(set(abb_filtered).union(set(cur_filtered)))
    # for abbreviation, currency in items:
    #     workflow.add_item(title=currency,
    #                       subtitle=abbreviation,
    #                       icon="icons/{0}.png".format(abbreviation),
    #                       valid=True,
    #                       arg=abbreviation)
    items = []
    for abbreviation, currency in currencies.items():
        if currencies_filter(query, abbreviation, currency, settings["currencies"]):
            items.append({
                "title": currency,
                "subtitle": abbreviation,
                "icon": "icons/{0}.png".format(abbreviation),
                "valid": True,
                "arg": abbreviation
            })
    items = sorted(items, key=lambda item: item["subtitle"])
    for item in items:
        workflow.add_item(**item)
    if not items:
        workflow.add_item(title="No Currency Found...",
                          subtitle="Perhaps trying something else?",
                          icon=ICON_WARNING)
        workflow.add_item(title="Kindly Notice",
                          subtitle="Your existed favorites won't show up in here",
                          icon=ICON_WARNING)
    workflow.send_feedback()

def load_favorite_currencies(workflow):
    """Load favorite currencies set in configs"""
    settings = workflow.settings
    config = load_config()
    currencies = load_currencies()
    if len(workflow.args) > 2:
        raise ValueError("One Currency at a time, please")
    args = workflow.args[1:]
    query = "" if not args else str(args[0]).upper()
    items = []
    for abbreviation in settings[currencies]:
        if currencies_filter(query, abbreviation, currencies[abbreviation]):
            items.append({
                "title": currencies[abbreviation],
                "subtitle": abbreviation,
                "icon": "icons/{0}.png".format(abbreviation),
                "valid": True,
                "arg": abbreviation
            })
    for item in items:
        workflow.add_item(**item)
    workflow.send_feedback()

def convert(workflow):
    """Run conversion patterns"""
    settings = workflow.settings
    config = load_config()
    rates = load_rates(settings)
    query = Query(workflow.args[1:])
    query.run_pattern(workflow, rates)
    workflow.send_feedback()

def add(workflow):
    currency = workflow.args[1]

    config = load_config()
    config.currencies.append(currency)
    config.save()

    settings = workflow.settings
    settings["currencies"].append(currency)
    settings.save()

    print(currency)

def remove(workflow):
    currency = workflow.args[1]

    config = load_config()
    config.currencies.remove(currency)
    config.save()

    settings = workflow.settings
    settings["currencies"].remove(currency)
    settings.save()

    print(currency)

def move(workflow):
    args = workflow.args[1:]

def base(workflow):
    currency = workflow.args[1]

    config = load_config()
    config.base = currency
    config.save()

    settings = workflow.settings
    settings["base"] = currency

    print(currency)

def help_me(workflow):
    workflow.add_item(title="cur",
                      subtitle="Convert 1 unit of all favorite currencies to base currency",
                      valid=True,
                      arg="cur")
    workflow.add_item(title="cur 200",
                      subtitle="Convert all favorite currencies with <value> to base currency",
                      valid=True,
                      arg="cur 200")
    workflow.add_item(title="cur GBP",
                      subtitle="Convert between <currency> and base currency with 1 unit",
                      valid=True,
                      arg="cur GBP")
    workflow.add_item(title="cur 5 GBP",
                      subtitle="Convert between <currency> and base currency with <value> unit",
                      valid=True,
                      arg="cur 5 GBP")
    workflow.add_item(title="cur GBP CAD",
                      subtitle="Convert between <currency_1> and <currency_2> with 1 unit",
                      valid=True,
                      arg="cur GBP CAD")
    workflow.add_item(title="cur 5 GBP CAD",
                      subtitle="Convert between <currency_1> and <currency_2> with <value> unit",
                      valid=True,
                      arg="cur 5 GBP CAD")
    workflow.send_feedback()
