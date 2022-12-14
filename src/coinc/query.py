"""Query parser and conversion mappings"""
from workflow import Workflow3

from .config import Config
from .exceptions import QueryError
from .utils import (
    currencies_filter,
    generate_result_item,
    is_it_alias,
    is_it_currency,
    is_it_float,
    is_it_something_mixed,
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

    def __init__(self, args: list, config: Config) -> None:
        self.value: float | None = None
        self.currency_one: str | None = None
        self.currency_two: str | None = None
        self.bit_pattern: int = 0
        self.binding: bool = False
        invalids = []
        for arg in args:
            value = is_it_float(arg)
            if value:
                self._fill_value(value)
                continue
            currency = is_it_currency(config, arg)
            if currency:
                self._fill_currency(currency)
                continue
            aliases = is_it_alias(arg)
            if aliases:
                self._fill_currency(aliases)
                continue
            mixed = is_it_something_mixed(config, arg)
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
                raise QueryError("Invalid Currencies", ", ".join(invalids))

    def _fill_value(self, value: float) -> float:
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

    def _fill_currency(self, currency: str, inplace: bool = False) -> str:
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

    def run_pattern(self, workflow: Workflow3) -> None:
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
        """
        workflow.logger.info(f"Run Pattern {self.bit_pattern}")
        workflow.logger.info(f"Value: {self.value}")
        workflow.logger.info(f"Currency One: {self.currency_one}")
        workflow.logger.info(f"Currency Two: {self.currency_two}")
        rates = load_rates(workflow.config)
        func = getattr(self, f"_pattern_{self.bit_pattern}")
        func(workflow, rates)

        # Show rates update time
        workflow.add_item(
            title="Last Update", subtitle=rates["last_update"], icon="hints/info.png"
        )

    def _pattern_0(self, workflow: Workflow3, rates: dict) -> None:
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

    def _pattern_1(self, workflow: Workflow3, rates: dict) -> None:
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

    def _pattern_2(self, workflow: Workflow3, rates: dict) -> None:
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

    def _pattern_3(self, workflow: Workflow3, rates: dict) -> None:
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

    def _pattern_4(self, workflow: Workflow3, rates: dict) -> None:
        """
        Method 4
        @#$ (broken currency)
        List possible currencies and redirect to Method 2
        """
        currencies = load_currencies()
        items = []
        for abbreviation in rates:
            currency = currencies.get(abbreviation, "")
            if currencies_filter(self.currency_two, abbreviation, currency):
                items.append(
                    dict(
                        title=currency,
                        subtitle=abbreviation,
                        icon=f"flags/{abbreviation}.png",
                        valid=True,
                        autocomplete=abbreviation,
                        arg=f"redirect,{abbreviation}",
                    )
                )
        items = sorted(items, key=lambda item: item["subtitle"])
        for item in items:
            workflow.add_item(**item)
        if not items:
            raise QueryError("Invalid Currency", self.currency_two)

    def _pattern_6(self, workflow: Workflow3, rates: dict) -> None:
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

    def _pattern_7(self, workflow: Workflow3, rates: dict) -> None:
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
