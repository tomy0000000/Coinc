# -*- coding: utf-8 -*-
"""Query parser and conversion mappings"""
from .exceptions import QueryError
from .utils import (
    currencies_filter,
    generate_result_item,
    is_it_currency,
    is_it_float,
    is_it_something_mixed,
    is_it_symbol,
    load_currencies,
    load_rates,
)


class Query:
    """Query parser and conversion mappings

    Arguments:
        args {list} -- list of arguments to filled

    Raises:
        QueryError -- Raised when invalid query were given
    """

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
                self._fill_value(value)
                continue
            currency = is_it_currency(arg)
            if currency:
                self._fill_currency(currency)
                continue
            symbol = is_it_symbol(arg)
            if symbol:
                self._fill_currency(symbol)
                continue
            mixed = is_it_something_mixed(arg)
            if mixed:
                self._fill_value(mixed[0])
                self._fill_currency(mixed[1], inplace=True)
                self.binding = True
                continue
            invalids.append(arg)
        if len(args) == 1 and self.bit_pattern == 0:
            # If there's only one argument, try to guess a currency
            try:
                self.currency_two = str(args[0])
            except UnicodeEncodeError:
                raise QueryError("Invalid Currency", args[0])
            self.bit_pattern += 4
        elif invalids:
            if len(invalids) == 1:
                raise QueryError("Invalid Currency", invalids[0])
            else:
                raise QueryError("Invalid Currencies", u", ".join(invalids))

    def _fill_value(self, value):
        """Fill value and run checks

        Arguments:
            value {float} -- Value to be filled in

        Returns:
            float -- Value that passed in

        Raises:
            QueryError -- Raised when there is no space to fill value
        """
        if not self.value:
            self.value = value
            self.bit_pattern += 1
            return value
        raise QueryError("Too many value", "Query can contain one numeric value only")

    def _fill_currency(self, currency, inplace=False):
        """Fill currency into proper position

        Arguments:
            currency {str} -- Currency code to be filled in

        Keyword Arguments:
            inplace {bool} -- If True, `currency` will be filled
                              into `currency_one`, old value will
                              moved to `currency_two` (default: {False})

        Returns:
            str -- Currency code that passed in

        Raises:
            QueryError -- Raised when there is no space to fill currency
        """
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
        raise QueryError(
            "Too many currencies", "Query can contain two currency code or symbol only"
        )

    def run_pattern(self, workflow):
        """Run Correspond Function by Pattern

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

        Arguments:
            workflow {workflow.Workflow3} -- workflow object
            rates {dict} -- dict containing rates
        """
        workflow.logger.info("Run Pattern {}".format(self.bit_pattern))
        rates = load_rates(workflow.config)
        func = getattr(self, "_pattern_{}".format(self.bit_pattern))
        func(workflow, rates)

        # Show rates update time
        workflow.add_item(
            title="Last Update", subtitle=rates["last_update"], icon="hints/info.png"
        )

    def _pattern_0(self, workflow, rates):
        """Run Pattern 0

        Query contains:
        | item         | Example Value |
        | ------------ | ------------- |
        | value        | <None>        |
        | currency_one | <None>        |
        | currency_two | <None>        |

        Results:
        1 <fav_1>  =  ? <base>
        1 <base>   =  ? <fav_1>
        1 <fav_2>  =  ? <base>
        1 <base>   =  ? <fav_2>
        ...

        Arguments:
            workflow {workflow.Workflow3} -- workflow object
            rates {dict} -- dict containing rates
        """
        for currency in workflow.settings["favorites"]:
            if workflow.config.orientation in ["DEFAULT", "FROM_FAV"]:
                generate_result_item(
                    workflow, 1, currency, workflow.config.base, rates, currency
                )
            if workflow.config.orientation in ["DEFAULT", "TO_FAV"]:
                generate_result_item(
                    workflow, 1, workflow.config.base, currency, rates, currency
                )

    def _pattern_1(self, workflow, rates):
        """Run Pattern 1

        Query contains:
        | item         | Example Value |
        | ------------ | ------------- |
        | value        | 5           |
        | currency_one | <None>        |
        | currency_two | <None>        |

        Results:
        5 <fav_1>  =  ? <base>
        5 <base>   =  ? <fav_1>
        5 <fav_2>  =  ? <base>
        5 <base>   =  ? <fav_2>
        ...

        Arguments:
            workflow {workflow.Workflow3} -- workflow object
            rates {dict} -- dict containing rates
        """
        for currency in workflow.settings["favorites"]:
            if workflow.config.orientation in ["DEFAULT", "FROM_FAV"]:
                generate_result_item(
                    workflow,
                    self.value,
                    currency,
                    workflow.config.base,
                    rates,
                    currency,
                )
            if workflow.config.orientation in ["DEFAULT", "TO_FAV"]:
                generate_result_item(
                    workflow,
                    self.value,
                    workflow.config.base,
                    currency,
                    rates,
                    currency,
                )

    def _pattern_2(self, workflow, rates):
        """Run Pattern 2

        Query contains:
        | item         | Example Value |
        | ------------ | ------------- |
        | value        | <None>        |
        | currency_one | GBP           |
        | currency_two | <None>        |

        Results:
        1 GBP      =  ? <base>
        1 <base>   =  ? GBP

        Arguments:
            workflow {workflow.Workflow3} -- workflow object
            rates {dict} -- dict containing rates
        """
        generate_result_item(
            workflow,
            1,
            self.currency_one,
            workflow.config.base,
            rates,
            self.currency_one,
        )
        generate_result_item(
            workflow,
            1,
            workflow.config.base,
            self.currency_one,
            rates,
            self.currency_one,
        )

    def _pattern_3(self, workflow, rates):
        """Run Pattern 3

        Query contains:
        | item         | Example Value |
        | ------------ | ------------- |
        | value        | 5             |
        | currency_one | GBP           |
        | currency_two | <None>        |

        Results:
        5 GBP      =  ? <base>
        5 <base>   =  ? GBP

        Arguments:
            workflow {workflow.Workflow3} -- workflow object
            rates {dict} -- dict containing rates
        """
        generate_result_item(
            workflow,
            self.value,
            self.currency_one,
            workflow.config.base,
            rates,
            self.currency_one,
        )
        if not self.binding:
            generate_result_item(
                workflow,
                self.value,
                workflow.config.base,
                self.currency_one,
                rates,
                self.currency_one,
            )

    def _pattern_4(self, workflow, rates):
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
                    dict(
                        title=currency,
                        subtitle=abbreviation,
                        icon="flags/{}.png".format(abbreviation),
                        valid=True,
                        autocomplete=abbreviation,
                        arg="redirect,{}".format(abbreviation),
                    )
                )
        items = sorted(items, key=lambda item: item["subtitle"])
        for item in items:
            workflow.add_item(**item)
        if not items:
            raise QueryError("Invalid Currency", self.currency_two)

    def _pattern_6(self, workflow, rates):
        """Run Pattern 6

        Query contains:
        | item         | Example Value |
        | ------------ | ------------- |
        | value        | <None>        |
        | currency_one | GBP           |
        | currency_two | CAD           |

        Results:
        1 GBP      =  ? CAD
        1 CAD      =  ? GBP

        Arguments:
            workflow {workflow.Workflow3} -- workflow object
            rates {dict} -- dict containing rates
        """
        generate_result_item(
            workflow, 1, self.currency_one, self.currency_two, rates, self.currency_two
        )
        generate_result_item(
            workflow, 1, self.currency_two, self.currency_one, rates, self.currency_one
        )

    def _pattern_7(self, workflow, rates):
        """Run Pattern 7

        Query contains:
        | item         | Example Value |
        | ------------ | ------------- |
        | value        | 5             |
        | currency_one | GBP           |
        | currency_two | CAD           |

        Results:
        5 GBP      =  ? CAD
        5 CAD      =  ? GBP

        Arguments:
            workflow {workflow.Workflow3} -- workflow object
            rates {dict} -- dict containing rates
        """
        generate_result_item(
            workflow,
            self.value,
            self.currency_one,
            self.currency_two,
            rates,
            self.currency_two,
        )
        if not self.binding:
            generate_result_item(
                workflow,
                self.value,
                self.currency_two,
                self.currency_one,
                rates,
                self.currency_one,
            )
