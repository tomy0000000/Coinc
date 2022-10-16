"""Functions to be called by workflow"""
import os
from datetime import datetime

from workflow import Workflow3

from .exceptions import CoincError, ConfigError
from .query import Query
from .utils import (
    generate_list_items,
    init_workflow,
    load_currencies,
    refresh_currencies,
    refresh_rates,
)

__all__ = [
    "load",
    "convert",
    "add",
    "remove",
    "arrange",
    "save_arrange",
    "refresh",
    "help_me",
]


def load(workflow: Workflow3) -> None:
    """Load all/favorites currencies"""
    currencies = load_currencies()
    if len(workflow.args) > 3:
        workflow.add_item(
            title="One Currency at a time, please", icon="hints/cancel.png"
        )
        workflow.send_feedback()
        return
    load_type = str(workflow.args[1])
    workflow.logger.info(load_type)
    args = workflow.args[2:]
    query = "" if not args else str(args[0]).upper()
    if os.getenv("redirect"):
        workflow.add_item(
            title="Done",
            subtitle="Dismiss",
            icon="hints/save.png",
            valid=True,
            arg="quit",
        )
    if load_type == "all":
        items = generate_list_items(
            query, list(currencies.keys()), workflow.settings["favorites"], True
        )
    elif load_type == "favorites":
        items = generate_list_items(query, workflow.settings["favorites"])
    for item in items:
        item = workflow.add_item(**item)
        item.setvar("redirect", True)
    if not items:
        workflow.add_item(
            title="No Currency Found...",
            subtitle="Perhaps trying something else?",
            icon="hints/info.png",
        )
        if load_type == "all":
            workflow.add_item(
                title="Kind notice",
                subtitle="Your existing favorites won't show up here",
                icon="hints/info.png",
            )
    workflow.send_feedback()


def convert(workflow: Workflow3) -> None:
    """Run conversion patterns"""
    try:
        init_workflow(workflow)
        query = Query(workflow.args[1:])
        query.run_pattern(workflow)
    except CoincError as error:
        workflow.logger.info(f"Coinc: {type(error).__name__}")
        workflow.logger.info(error)
        workflow.add_item(
            title=error.args[0], subtitle=error.args[1], icon="hints/cancel.png"
        )
    workflow.send_feedback()


def add(workflow: Workflow3) -> None:
    """Add currency to favorite list"""
    currency = workflow.args[1]
    workflow.settings["favorites"].append(currency)
    workflow.settings.save()
    currencies = load_currencies()
    print(f"{currencies[currency]} ({currency})")


def remove(workflow: Workflow3) -> None:
    """Remove currency from favorite list"""
    currency = workflow.args[1]
    workflow.settings["favorites"].remove(currency)
    workflow.settings.save()
    currencies = load_currencies()
    print(f"{currencies[currency]} ({currency})")


def arrange(workflow: Workflow3) -> None:
    """Rearrange favorite currencies order"""
    currencies = load_currencies()
    favorites = workflow.settings["favorites"]
    args = workflow.args[1:]
    if len(args) == len(favorites):
        workflow.add_item(
            title="Save",
            subtitle="Save current arrangement",
            icon="hints/save.png",
            valid=True,
            arg=f"save {' '.join(args)}",
        )
        workflow.add_item(
            title="Cancel",
            subtitle="Cancel the operation without saving",
            icon="hints/cancel.png",
            valid=True,
            arg=f"cancel {' '.join(args)}",
        )
    for abbreviation in favorites:
        if abbreviation not in args:
            query = f"{' '.join(args)} {abbreviation}" if args else abbreviation
            workflow.add_item(
                title=currencies[abbreviation],
                subtitle=abbreviation,
                icon=f"flags/{abbreviation}.png",
                valid=True,
                arg=query,
                autocomplete=query,
            )
    if args:
        workflow.add_item(title="---------- Begin New Arrangement ----------")
    for arg in args:
        if arg in favorites:
            workflow.add_item(
                title=currencies[arg], subtitle=arg, icon=f"flags/{arg}.png"
            )
        else:
            workflow.add_item(
                title=f"Currency {arg} isn't in favortie list",
                icon="hints/cancel.png",
            )
            workflow.send_feedback()
            return None
    if args:
        workflow.add_item(title="---------- End New Arrangement ----------")
    workflow.add_item(
        title="To insert, press Return or Tab on selected item", icon="hints/info.png"
    )
    workflow.add_item(
        title="To remove last item, press Option-Delete", icon="hints/info.png"
    )
    workflow.send_feedback()


def save_arrange(workflow: Workflow3) -> None:
    """Save new favorite arrangement"""
    args = workflow.args[2:]
    workflow.logger.info(args)
    workflow.settings["favorites"] = [str(arg) for arg in args]
    print(" ".join(args))


def refresh(workflow: Workflow3) -> None:
    """Manually trigger rates refresh"""
    try:
        init_workflow(workflow)
    except ConfigError as error:
        workflow.logger.info(error)
        workflow.add_item(
            title=error.args[0], subtitle=error.args[1], icon="hints/cancel.png"
        )
    try:
        refresh_rates(workflow.config)
        refresh_currencies()
    except CoincError as error:
        workflow.logger.info(error)
        print(f"❌ Error occured during refresh,Coinc: {type(error).__name__}")
    print(f"✅ Currency list and rates have refreshed,{datetime.now()}")


def help_me(workflow: Workflow3) -> None:
    """Function for showing example usage"""
    workflow.add_item(
        title="cur",
        subtitle="Convert between all favorite currencies and base currency with 1 unit",
        valid=True,
        arg="cur",
    )
    workflow.add_item(
        title="cur 200",
        subtitle="Convert between all favorite currencies and base currency with <value> unit",
        valid=True,
        arg="cur 200",
    )
    workflow.add_item(
        title="cur GBP",
        subtitle="Convert between <currency> and base currency with 1 unit",
        valid=True,
        arg="cur GBP",
    )
    workflow.add_item(
        title="cur 5 GBP",
        subtitle="Convert between <currency> and base currency with <value> unit",
        valid=True,
        arg="cur 5 GBP",
    )
    workflow.add_item(
        title="cur GBP CAD",
        subtitle="Convert between <currency_1> and <currency_2> with 1 unit",
        valid=True,
        arg="cur GBP CAD",
    )
    workflow.add_item(
        title="cur 5 GBP CAD",
        subtitle="Convert between <currency_1> and <currency_2> with <value> unit",
        valid=True,
        arg="cur 5 GBP CAD",
    )
    workflow.add_item(
        title="cur-add CAD",
        subtitle="Add CAD to favorite list",
        icon="hints/gear.png",
        valid=True,
        arg="cur-add CAD",
    )
    workflow.add_item(
        title="cur-rm GBP",
        subtitle="Remove GBP from favorite list",
        icon="hints/gear.png",
        valid=True,
        arg="cur-rm GBP",
    )
    workflow.add_item(
        title="cur-arr",
        subtitle="Arrange orders of the favorite list",
        icon="hints/gear.png",
        valid=True,
        arg="cur-arr",
    )
    workflow.add_item(
        title="cur-ref",
        subtitle="Refresh Currency List & Rates",
        icon="hints/gear.png",
        valid=True,
        arg="cur-ref",
    )
    workflow.add_item(
        title="Documentation",
        subtitle="Select this to find out more comprehensive documentation",
        icon="hints/info.png",
        valid=True,
        arg="cur workflow:help",
    )
    workflow.send_feedback()
