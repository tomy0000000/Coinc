# -*- coding: utf-8 -*-
"""Parse query into machine-readable format"""
from .config import Config
from .utils import (is_it_float, is_it_currency, is_it_currency_symbol,
                    is_it_something_mixed, calculate, load_currencies,
                    currencies_filter)


class Query():
    """Parse query into machine-readable format"""
    def __init__(self, args):
        self.value = None
        self.currency_one = None
        self.currency_two = None
        self.bit_pattern = 0
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
            symbol_currency = is_it_currency_symbol(arg)
            if symbol_currency:
                self.fill_currency(symbol_currency)
                continue
            mixed = is_it_something_mixed(arg)
            if mixed:
                self.fill_value(mixed[0])
                self.fill_currency(mixed[1])
                continue
            invalids.append(arg)
        if len(args) == 1 and self.bit_pattern == 0:
            # If there's only one argument, try to guess a currency
            try:
                self.currency_two = str(args[0])
            except UnicodeEncodeError:
                raise ValueError(u"Invalid Currency: {}".format(args[0]))
            self.bit_pattern += 4
        elif invalids:
            if len(invalids) == 1:
                raise ValueError(u"Invalid Currency: {}".format(invalids[0]))
            else:
                raise ValueError(u"Invalid Currencies: {}".format(
                    ", ".join(invalids)))

    def fill_value(self, value):
        """Run checks before insert value"""
        if not self.value:
            self.value = value
            self.bit_pattern += 1
            return value
        raise ValueError("Too many Value")

    def fill_currency(self, currency):
        """Fill currency into proper position"""
        if not self.currency_one:
            self.currency_one = str(currency)
            self.bit_pattern += 2
            return currency
        if not self.currency_two:
            self.currency_two = str(currency)
            self.bit_pattern += 4
            return currency
        raise ValueError("Too many Currencies")

    def run_pattern(self, workflow, rates):
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
        func(workflow, rates)

    def pattern_0(self, workflow, rates):
        """
        Method 0
        Convert between all favorite currencies and base currency with 1 unit
        """
        config = Config()
        settings = workflow.settings
        for currency in settings["favorites"]:
            converted = calculate(1, currency, config.base, rates)
            item_1 = workflow.add_item(
                title="1 {} = {} {}".format(currency, converted, config.base),
                subtitle="Last Update: {}".format(rates["last_update"]),
                icon="flags/{}.png".format(currency),
                valid=True,
                arg=str(converted),
                copytext=str(converted))
            # item_1.add_modifier(key="cmd",
            #                   subtitle="cmd-subtitle",
            #                   icon="flags/{}.png".format(currency),
            #                   valid=True,
            #                   arg="${}".format(str(converted)))
            # item_1.add_modifier(key="alt",
            #                   subtitle="alt-subtitle",
            #                   valid=True,
            #                   arg=str(converted))
            # item_1.add_modifier(key="ctrl",
            #                   subtitle="ctrl-subtitle",
            #                   valid=True,
            #                   arg=str(converted))
            # item_1.add_modifier(key="shift",
            #                   subtitle="shift-subtitle",
            #                   valid=True,
            #                   arg=str(converted))
            # item_1.add_modifier(key="fn",
            #                   subtitle="fn-subtitle",
            #                   valid=True,
            #                   arg=str(converted))
            converted = calculate(1, config.base, currency, rates)
            item_2 = workflow.add_item(
                title="1 {} = {} {}".format(config.base, converted, currency),
                subtitle="Last Update: {}".format(rates["last_update"]),
                icon="flags/{}.png".format(currency),
                valid=True,
                arg=str(converted),
                copytext=str(converted))

    def pattern_1(self, workflow, rates):
        """
        Method 1
        100 (value)
        Convert between all favorite currencies and base currency with [value] unit
        """
        config = Config()
        settings = workflow.settings
        for currency in settings["favorites"]:
            converted = calculate(self.value, currency, config.base, rates)
            workflow.add_item(
                title="{} {} = {} {}".format(self.value, currency, converted,
                                             config.base),
                subtitle="Last Update: {}".format(rates["last_update"]),
                icon="flags/{}.png".format(currency),
                valid=True,
                arg=str(converted))
            converted = calculate(self.value, config.base, currency, rates)
            workflow.add_item(
                title="{} {} = {} {}".format(self.value, config.base,
                                             converted, currency),
                subtitle="Last Update: {}".format(rates["last_update"]),
                icon="flags/{}.png".format(currency),
                valid=True,
                arg=str(converted))

    def pattern_2(self, workflow, rates):
        """
        Method 2
        GBP (currency)
        Convert 1 (currency) to (base)
        Convert 1 (base) to (currency)
        """
        config = Config()
        converted_one = calculate(1, self.currency_one, config.base, rates)
        workflow.add_item(
            title="1 {} = {} {}".format(self.currency_one, converted_one,
                                        config.base),
            subtitle="Last Update: {}".format(rates["last_update"]),
            icon="flags/{}.png".format(self.currency_one),
            valid=True,
            arg=str(converted_one))
        converted_two = calculate(1, config.base, self.currency_one, rates)
        workflow.add_item(
            title="1 {} = {} {}".format(config.base, converted_two,
                                        self.currency_one),
            subtitle="Last Update: {}".format(rates["last_update"]),
            icon="flags/{}.png".format(self.currency_one),
            valid=True,
            arg=str(converted_two))

    def pattern_3(self, workflow, rates):
        """
        Method 3
        5 GBP (value, currency)
        Convert 5 (currency) to (base)
        Convert 5 (base) to (currency)
        """
        config = Config()
        converted_one = calculate(self.value, self.currency_one, config.base,
                                  rates)
        workflow.add_item(
            title="{} {} = {} {}".format(self.value, self.currency_one,
                                         converted_one, config.base),
            subtitle="Last Update: {}".format(rates["last_update"]),
            icon="flags/{}.png".format(self.currency_one),
            valid=True,
            arg=str(converted_one))
        converted_two = calculate(self.value, config.base, self.currency_one,
                                  rates)
        workflow.add_item(
            title="{} {} = {} {}".format(self.value, config.base,
                                         converted_two, self.currency_one),
            subtitle="Last Update: {}".format(rates["last_update"]),
            icon="flags/{}.png".format(self.currency_one),
            valid=True,
            arg=str(converted_two))

    def pattern_4(self, workflow, rates):
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
                         subtitle="Last Update: {}".format(
                             rates["last_update"]),
                         icon="flags/{}.png".format(abbreviation),
                         valid=True,
                         autocomplete=abbreviation,
                         arg="redirect,{}".format(abbreviation)))
        items = sorted(items, key=lambda item: item["subtitle"])
        for item in items:
            workflow.add_item(**item)
        if not items:
            raise ValueError("Invalid Currency: {}".format(self.currency_two))

    def pattern_6(self, workflow, rates):
        """
        Method 6
        GBP CAD (currency_1, currency_2)
        Convert 1 (currency_1) to (currency_2)
        Convert 1 (currency_2) to (currency_1)
        """
        converted_one = calculate(1, self.currency_one, self.currency_two,
                                  rates)
        workflow.add_item(
            title="1 {} = {} {}".format(self.currency_one, converted_one,
                                        self.currency_two),
            subtitle="Last Update: {}".format(rates["last_update"]),
            icon="flags/{}.png".format(self.currency_two),
            valid=True,
            arg=str(converted_one))
        converted_two = calculate(1, self.currency_two, self.currency_one,
                                  rates)
        workflow.add_item(
            title="1 {} = {} {}".format(self.currency_two, converted_two,
                                        self.currency_one),
            subtitle="Last Update: {}".format(rates["last_update"]),
            icon="flags/{}.png".format(self.currency_one),
            valid=True,
            arg=str(converted_two))

    def pattern_7(self, workflow, rates):
        """
        Method 7
        5 GBP CAD (value, currency_1, currency_2)
        Convert (value) (currency_1) to (currency_2)
        Convert (value) (currency_2) to (currency_1)
        """
        converted_one = calculate(self.value, self.currency_one,
                                  self.currency_two, rates)
        workflow.add_item(
            title="{} {} = {} {}".format(self.value, self.currency_one,
                                         converted_one, self.currency_two),
            subtitle="Last Update: {}".format(rates["last_update"]),
            icon="flags/{}.png".format(self.currency_two),
            valid=True,
            arg=str(converted_one))
        converted_two = calculate(self.value, self.currency_two,
                                  self.currency_one, rates)
        workflow.add_item(
            title="{} {} = {} {}".format(self.value, self.currency_two,
                                         converted_two, self.currency_one),
            subtitle="Last Update: {}".format(rates["last_update"]),
            icon="flags/{}.png".format(self.currency_one),
            valid=True,
            arg=str(converted_two))
