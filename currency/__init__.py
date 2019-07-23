"""Function to be called by workflow"""
from .query import Query
from .utils import load_config, load_rates, load_currencies, calculate

__all__ = ["convert", "load", "add", "remove", "modify", "base", "help"]

def convert(workflow):
    config = load_config()
    workflow.logger.info(str(config.__dict__))
    rates = load_rates(config)
    # workflow.logger.info(rates)
    query = Query(workflow.args[1:])
    workflow.add_item(title="query", subtitle=config.__dict__)
    query.run_pattern(workflow, config, rates)
    workflow.send_feedback()

def load(workflow):
    """Load all available currencies"""
    currencies = load_currencies()
    for abbreviation, currency in currencies.items():
        workflow.add_item(title=currency,
                          subtitle=abbreviation,
                          icon="icons/{0}.png".format(abbreviation),
                          valid=True,
                          arg=abbreviation)
    workflow.send_feedback()

def add(workflow):
    args = workflow.args[1:]

def remove(workflow):
    args = workflow.args[1:]

def modify(workflow):
    args = workflow.args[1:]

def base(workflow):
    args = workflow.args[1:]

def help(workflow):
    workflow.add_item(title="")
