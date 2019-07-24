"""Function to be called by workflow"""
from .query import Query
from .utils import load_config, load_rates, load_currencies, calculate, currencies_filter

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
    config = load_config()
    currencies = load_currencies()
    workflow.args.pop(0)
    if len(workflow.args) > 2:
        raise ValueError("One Currency at a time, please")
    args = workflow.args[1:]
    query = "" if not args else str(args[0]).upper()
    workflow.logger.info("query: {}".format(query))
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
        if currencies_filter(query, abbreviation, currency, config):
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
                          subtitle="Perhaps trying something else?")
        workflow.add_item(title="Kindly Notice",
                          subtitle="Your existed favorites won't show up in here")
    workflow.send_feedback()

def load_favorite_currencies(workflow):
    """Load favorite currencies set in configs"""
    config = load_config()
    currencies = load_currencies()
    for abbreviation in config.currencies:
        workflow.add_item(title=currencies[abbreviation],
                          subtitle=abbreviation,
                          icon="icons/{0}.png".format(abbreviation),
                          valid=True,
                          arg=abbreviation)
    workflow.send_feedback()

def convert(workflow):
    """Run conversion patterns"""
    config = load_config()
    # workflow.logger.info(str(config.__dict__))
    rates = load_rates(config)
    query = Query(workflow.args[1:])
    # workflow.add_item(title="query", subtitle=config.__dict__)
    query.run_pattern(workflow, config, rates)
    workflow.send_feedback()

def add(workflow):
    currency = workflow.args[1]
    config = load_config()
    config.currencies.append(currency)
    config.save()
    print(currency)

def remove(workflow):
    currency = workflow.args[1]
    config = load_config()
    config.currencies.remove(currency)
    config.save()
    print(currency)

def move(workflow):
    args = workflow.args[1:]

def base(workflow):
    args = workflow.args[1:]

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
