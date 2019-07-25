"""Query"""
from .utils import is_it_currency, is_it_float, is_it_something_mixed, calculate

class Query():
    """Parse query into machine-readable format"""
    def __init__(self, args):
        self.value = None
        self.currency_one = None
        self.currency_two = None
        self.bit_pattern = 0
        for arg in args:
            value = is_it_float(arg)
            if value:
                self.fill_value(value)
                continue
            currency = is_it_currency(arg)
            if currency:
                self.fill_currency(currency)
                continue
            mixed = is_it_something_mixed(arg)
            if mixed:
                self.fill_value(mixed[0])
                self.fill_currency(mixed[1])
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
        """Run Correspond Function by Pattern"""
        workflow.logger.info("Run Pattern {0}".format(self.bit_pattern))
        func = getattr(self, "pattern_{0}".format(self.bit_pattern))
        func(workflow, rates)
    def pattern_0(self, workflow, rates):
        """
        Method 0
        Convert all currencies with value 1 to base
        """
        settings = workflow.settings
        for currency in settings["currencies"]:
            converted = calculate(1, currency, settings["base"], settings, rates)
            item = workflow.add_item(title="1 {0} = {1} {2}".format(currency, converted, settings["base"]),
                                     subtitle=currency,
                                     icon="icons/{0}.png".format(currency),
                                     valid=True,
                                     arg=str(converted),
                                     copytext=str(converted))
            # item.add_modifier(key="cmd",
            #                   subtitle="cmd-subtitle",
            #                   valid=True,
            #                   arg=str(converted))
            # item.add_modifier(key="alt",
            #                   subtitle="alt-subtitle",
            #                   valid=True,
            #                   arg=str(converted))
            # item.add_modifier(key="ctrl",
            #                   subtitle="ctrl-subtitle",
            #                   valid=True,
            #                   arg=str(converted))
            # item.add_modifier(key="shift",
            #                   subtitle="shift-subtitle",
            #                   valid=True,
            #                   arg=str(converted))
            # item.add_modifier(key="fn",
            #                   subtitle="fn-subtitle",
            #                   valid=True,
            #                   arg=str(converted))
    def pattern_1(self, workflow, rates):
        """
        Method 1
        100 (value)
        Convert all currencies with value (value) to base
        """
        settings = workflow.settings
        for currency in settings["currencies"]:
            converted = calculate(self.value, currency, settings["base"], settings, rates)
            workflow.add_item(title="{0} {1} = {2} {3}".format(
                self.value, currency, converted, settings["base"]),
                              subtitle=currency,
                              icon="icons/{0}.png".format(currency),
                              valid=True,
                              arg=str(converted))
    def pattern_2(self, workflow, rates):
        """
        Method 2
        GBP (currency)
        Convert 1 (currency) to (base)
        Convert 1 (base) to (currency)
        """
        settings = workflow.settings
        converted_one = calculate(1, self.currency_one, settings["base"], settings, rates)
        workflow.add_item(title="1 {0} = {1} {2}".format(
            self.currency_one, converted_one, settings["base"]),
                          icon="icons/{0}.png".format(self.currency_one),
                          valid=True,
                          arg=str(converted_one))
        converted_two = calculate(1, settings["base"], self.currency_one, settings, rates)
        workflow.add_item(title="1 {0} = {1} {2}".format(
            settings["base"], converted_two, self.currency_one),
                          icon="icons/{0}.png".format(self.currency_one),
                          valid=True,
                          arg=str(converted_two))
    def pattern_3(self, workflow, rates):
        """
        Method 3
        5 GBP (value, currency)
        Convert 5 (currency) to (base)
        Convert 5 (base) to (currency)
        """
        settings = workflow.settings
        converted_one = calculate(self.value, self.currency_one, settings["base"], settings, rates)
        workflow.add_item(title="{0} {1} = {2} {3}".format(
            self.value, self.currency_one, converted_one, settings["base"]),
                          icon="icons/{0}.png".format(self.currency_one),
                          valid=True,
                          arg=str(converted_one))
        converted_two = calculate(self.value, settings["base"], self.currency_one, settings, rates)
        workflow.add_item(title="{0} {1} = {2} {3}".format(
            self.value, settings["base"], converted_two, self.currency_one),
                          icon="icons/{0}.png".format(self.currency_one),
                          valid=True,
                          arg=str(converted_two))
    def pattern_6(self, workflow, rates):
        """
        Method 4
        GBP CAD (currency_1, currency_2)
        Convert 1 (currency_1) to (currency_2)
        Convert 1 (currency_2) to (currency_1)
        """
        settings = workflow.settings
        converted_one = calculate(1, self.currency_one, self.currency_two, settings, rates)
        workflow.add_item(title="1 {0} = {1} {2}".format(
            self.currency_one, converted_one, self.currency_two),
                          icon="icons/{0}.png".format(self.currency_two),
                          valid=True,
                          arg=str(converted_one))
        converted_two = calculate(1, self.currency_two, self.currency_one, settings, rates)
        workflow.add_item(title="1 {0} = {1} {2}".format(
            self.currency_two, converted_two, self.currency_one),
                          icon="icons/{0}.png".format(self.currency_one),
                          valid=True,
                          arg=str(converted_two))
    def pattern_7(self, workflow, rates):
        """
        Method 5
        5 GBP CAD (value, currency_1, currency_2)
        Convert (value) (currency_1) to (currency_2)
        Convert (value) (currency_2) to (currency_1)
        """
        settings = workflow.settings
        converted_one = calculate(self.value, self.currency_one, self.currency_two, settings, rates)
        workflow.add_item(title="{0} {1} = {2} {3}".format(
            self.value, self.currency_one, converted_one, self.currency_two),
                          icon="icons/{0}.png".format(self.currency_two),
                          valid=True,
                          arg=str(converted_one))
        converted_two = calculate(self.value, self.currency_two, self.currency_one, settings, rates)
        workflow.add_item(title="{0} {1} = {2} {3}".format(
            self.value, self.currency_two, converted_two, self.currency_one),
                          icon="icons/{0}.png".format(self.currency_one),
                          valid=True,
                          arg=str(converted_two))
