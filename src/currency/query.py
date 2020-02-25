# -*- coding: utf-8 -*-
"""Parse query into machine-readable format"""
from .config import Config
from .exceptions import QueryError
from .utils import (is_it_float, is_it_currency, is_it_symbol,
                    is_it_something_mixed, load_currencies, load_rates,
                    currencies_filter, generate_result_items)


class Query():
    """Parse query into machine-readable format"""
    def __init__(self, args):
        self.value = None
        self.currency_one = None
        self.currency_two = None
        self.bit_pattern = 0
        self.binding = False
        invalids = []
        for arg in args:
            value = is_it_float(arg)
            if value:
                self.fill_value(value)
                continue
            currency = is_it_currency(arg)
            if currency:
                self.fill_currency(currency)
                continue
            symbol = is_it_symbol(arg)
            if symbol:
                self.fill_currency(symbol)
                continue
            mixed = is_it_something_mixed(arg)
            if mixed:
                self.fill_value(mixed[0])
                self.fill_currency(mixed[1], inplace=True)
                self.binding = True
                continue
            invalids.append(arg)
        if len(args) == 1 and self.bit_pattern == 0:
            # If there's only one argument, try to guess a currency
            try:
                self.currency_two = str(args[0])
            except UnicodeEncodeError:
                raise QueryError(u"Invalid Currency: {}".format(args[0]))
            self.bit_pattern += 4
        elif invalids:
            if len(invalids) == 1:
                raise QueryError(u"Invalid Currency: {}".format(invalids[0]))
            else:
                raise QueryError(u"Invalid Currencies: {}".format(
                    ", ".join(invalids)))

    def fill_value(self, value):
        """Run checks before insert value"""
        if not self.value:
            self.value = value
            self.bit_pattern += 1
            return value
        raise QueryError("Too many Value")

    def fill_currency(self, currency, inplace=False):
        """Fill currency into proper position"""
        if not self.currency_one:
            self.currency_one = str(currency)
            self.bit_pattern += 2
            return currency
        if inplace and self.currency_one:
            currency, self.currency_one = self.currency_one, currency
        if not self.currency_two:
            self.currency_two = str(currency)
            self.bit_pattern += 4
            return currency
        raise QueryError("Too many Currencies")

    def run_pattern(self, workflow):
        """
        Run Correspond Function by Pattern
        | Pattern | currency_two | currency_one | value |
        | ------- | ------------ | ------------ | ----- |
        | 0       | 0            | 0            | 0     |
        | 1       | 0            | 0            | 1     |
        | 2       | 0            | 1            | 0     |
        | 3       | 0            | 1            | 1     |
        | 4       | 1            | 0            | 0     |
        | 5       | 1            | 0            | 1     | -> Undefined
        | 6       | 1            | 1            | 0     |
        | 7       | 1            | 1            | 1     |
        """
        workflow.logger.info("Run Pattern {}".format(self.bit_pattern))
        func = getattr(self, "pattern_{}".format(self.bit_pattern))
        func(workflow)

    def pattern_0(self, workflow):
        """
        Method 0
        Convert between all favorite currencies and base currency with 1 unit
        """
        config = Config()
        settings = workflow.settings
        rates = load_rates()
        # Show rates update time
        workflow.add_item(title="Last Update",
                          subtitle=rates["last_update"],
                          icon="hints/info.png")
        for currency in settings["favorites"]:
            if config.orientation in ["DEFAULT", "FROM_FAV"]:
                generate_result_items(workflow, 1, currency, config.base,
                                      rates, currency)
            if config.orientation in ["DEFAULT", "TO_FAV"]:
                generate_result_items(workflow, 1, config.base, currency,
                                      rates, currency)

    def pattern_1(self, workflow):
        """
        Method 1
        100 (value)
        Convert between all favorite currencies and base currency with [value] unit
        """
        config = Config()
        settings = workflow.settings
        rates = load_rates()
        # Show rates update time
        workflow.add_item(title="Last Update",
                          subtitle=rates["last_update"],
                          icon="hints/info.png")
        for currency in settings["favorites"]:
            if config.orientation in ["DEFAULT", "FROM_FAV"]:
                generate_result_items(workflow, self.value, currency,
                                      config.base, rates, currency)
            if config.orientation in ["DEFAULT", "TO_FAV"]:
                generate_result_items(workflow, self.value, config.base,
                                      currency, rates, currency)

    def pattern_2(self, workflow):
        """
        Method 2
        GBP (currency)
        Convert 1 (currency) to (base)
        Convert 1 (base) to (currency)
        """
        config = Config()
        rates = load_rates()
        generate_result_items(workflow, 1, self.currency_one, config.base,
                              rates, self.currency_one)
        generate_result_items(workflow, 1, config.base, self.currency_one,
                              rates, self.currency_one)

    def pattern_3(self, workflow):
        """
        Method 3
        5 GBP (value, currency)
        Convert 5 (currency) to (base)
        Convert 5 (base) to (currency) -> only show when not binding
        """
        config = Config()
        rates = load_rates()
        generate_result_items(workflow, self.value, self.currency_one,
                              config.base, rates, self.currency_one)
        if not self.binding:
            generate_result_items(workflow, self.value, config.base,
                                  self.currency_one, rates, self.currency_one)

    def pattern_4(self, workflow):
        """
        Method 4
        @#$ (broken currency)
        List possible currencies and redirect to Method 2
        """
        currencies = load_currencies()
        items = []
        for abbreviation, currency in currencies.items():
            if currencies_filter(self.currency_two, abbreviation, currency):
                items.append(
                    dict(title=currency,
                         subtitle=abbreviation,
                         icon="flags/{}.png".format(abbreviation),
                         valid=True,
                         autocomplete=abbreviation,
                         arg="redirect,{}".format(abbreviation)))
        items = sorted(items, key=lambda item: item["subtitle"])
        for item in items:
            workflow.add_item(**item)
        if not items:
            raise QueryError(u"Invalid Currency: {}".format(self.currency_two))

    def pattern_6(self, workflow):
        """
        Method 6
        GBP CAD (currency_1, currency_2)
        Convert 1 (currency_1) to (currency_2)
        Convert 1 (currency_2) to (currency_1)
        """
        rates = load_rates()
        generate_result_items(workflow, 1, self.currency_one,
                              self.currency_two, rates, self.currency_two)
        generate_result_items(workflow, 1, self.currency_two,
                              self.currency_one, rates, self.currency_one)

    def pattern_7(self, workflow):
        """
        Method 7
        5 GBP CAD (value, currency_1, currency_2)
        Convert (value) (currency_1) to (currency_2)
        Convert (value) (currency_2) to (currency_1) -> only show when not binding
        """
        rates = load_rates()
        generate_result_items(workflow, self.value, self.currency_one,
                              self.currency_two, rates, self.currency_two)
        if not self.binding:
            generate_result_items(workflow, self.value, self.currency_two,
                                  self.currency_one, rates, self.currency_one)
