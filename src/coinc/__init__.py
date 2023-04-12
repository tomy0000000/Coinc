"""💰💱 Alfred Workflow for currencies conversion"""
import os
from datetime import datetime

from workflow import Workflow3

from .alfred import persisted_data
from .exceptions import CoincError, ConfigError
from .query import Query
from .utils import (
    add_alias,
    currencies_filter,
    generate_list_items,
    init_workflow,
    load_currencies,
    refresh_currencies,
    refresh_rates,
    remove_alias,
)

__version__ = "3.1.1"
__all__ = [
    "load",
    "convert",
    "add",
    "remove",
    "arrange",
    "save_arrange",
    "refresh",
    "alias",
    "save_alias",
    "unalias",
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
        query = Query(workflow.args[1:], workflow.config)
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


def alias(workflow: Workflow3) -> None:
    """Check if alias exists"""
    aliases = persisted_data("alias")
    currencies = load_currencies()
    workflow.logger.info(f"{workflow.args=}")

    alias = workflow.args[1].upper() if len(workflow.args) > 1 else ""
    query = workflow.args[2].upper() if len(workflow.args) > 2 else ""

    if len(workflow.args) > 3:
        workflow.add_item(
            title="Too many arguments",
            subtitle="Usage: cur-alias <alias> <currency>",
            icon="hints/cancel.png",
        )
    elif not alias:
        # No alias is provided, hint user to type one
        workflow.add_item(
            title="Type the alias",
            subtitle="valid alias should not contain digits",
            icon="hints/gear.png",
        )
    elif alias in aliases:
        # Alias already exists
        currency = aliases[alias]
        workflow.add_item(
            title=f"{alias} is already aliased",
            subtitle=f"to {currencies[currency]} ({currency})",
            icon=f"flags/{currency}.png",
        )
    elif any(char.isdigit() for char in alias):
        # Alias contains number
        workflow.add_item(
            title="Can't create alias with number in it",
            icon="hints/cancel.png",
        )
    elif query in currencies:
        # Arguments are valid, confirm to save
        workflow.add_item(
            title=f"Alias {alias} to {currencies[query]} ({query})",
            subtitle="Confirm to save",
            icon=f"flags/{query}.png",
            valid=True,
            arg=f"create,{alias},{query}",
        )
    else:
        # Alias is valid, currency is empty or invalid code, suggest currencies
        items = generate_list_items(query, list(currencies.keys()))
        if items:
            workflow.add_item(
                title=f"Alias '{alias}' to ...",
                subtitle="Type the currency (name or code) after alias with space to search",
                icon="hints/info.png",
            )
            for item in items:
                code = item["arg"]
                item["arg"] = f"redirect,{alias} {code}"
                item = workflow.add_item(**item)
        else:
            workflow.add_item(
                title=f"No currency found for '{query}'",
                icon="hints/cancel.png",
            )
    workflow.send_feedback()


def unalias(workflow: Workflow3) -> None:
    """Remove alias"""
    aliases = persisted_data("alias")
    currencies = load_currencies()
    if len(workflow.args) < 3:
        query = workflow.args[1].upper() if len(workflow.args) == 2 else ""
        for alias in aliases:
            code = aliases[alias]
            currency = currencies[code]
            if currencies_filter(query, code, currency) or query in alias:
                workflow.add_item(
                    title=f"'{alias}' is aliased to {currency} ({code})",
                    subtitle="Press enter to confirm unalias",
                    icon=f"flags/{code}.png",
                    valid=True,
                    arg=f"remove,{alias},{code}",
                )
        if not workflow._items:
            workflow.add_item(
                title=f"Alias '{query}' not found",
                icon="hints/cancel.png",
            )
    else:
        workflow.add_item(
            title="Too many arguments",
            subtitle="Usage: cur-unalias <alias>",
            icon="hints/cancel.png",
        )
    workflow.send_feedback()


def save_alias(workflow: Workflow3) -> None:
    """Save alias"""
    action, alias, currency = workflow.args[1].split(",")
    alias = alias.upper()
    if action == "create":
        add_alias(alias, currency)
        print(f"✅ Currency alias created,{alias} → {currency}")
    elif action == "remove":
        remove_alias(alias)
        print(f"✅ Currency alias removed,{alias} → {currency}")
    else:
        print(f"❌ Invalid action,{action}")


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
        title="cur GBP TWD",
        subtitle="Convert between <currency_1> and <currency_2> with 1 unit",
        valid=True,
        arg="cur GBP TWD",
    )
    workflow.add_item(
        title="cur 5 GBP TWD",
        subtitle="Convert between <currency_1> and <currency_2> with <value> unit",
        valid=True,
        arg="cur 5 GBP TWD",
    )
    workflow.add_item(
        title="cur-add TWD",
        subtitle="Add TWD to favorite list",
        icon="hints/gear.png",
        valid=True,
        arg="cur-add TWD",
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
        subtitle="Refresh currency list & rates",
        icon="hints/gear.png",
        valid=True,
        arg="cur-ref",
    )
    workflow.add_item(
        title="cur-index",
        subtitle="Add alias keyword triggers",
        icon="hints/gear.png",
        valid=True,
        arg="cur-index",
    )
    workflow.add_item(
        title="cur-alias 新台幣 TWD",
        subtitle="Add '新台幣' as alias to match it to TWD",
        icon="hints/gear.png",
        valid=True,
        arg="cur-alias 新台幣 TWD",
    )
    workflow.add_item(
        title="Documentation",
        subtitle="See documentation for more comprehensive usage",
        icon="hints/info.png",
        valid=True,
        arg="cur workflow:help",
    )
    workflow.send_feedback()
