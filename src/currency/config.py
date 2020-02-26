# -*- coding: utf-8 -*-
"""Helper class for loading config set in Alfred Variable Sheet"""
import os
from .exceptions import ConfigError
from .utils import load_currencies


class Config():
    """Helper class for loading config set in Alfred Environment Variables Sheet

    Raises:
        ConfigError -- Raised when there are invalid value
                       filled in Configuration Sheet
    """
    def __init__(self):
        # App_ID
        app_id = os.getenv("APP_ID")
        if not app_id:
            raise ConfigError("Please setup APP_ID to refresh new rates",
                              ("Paste your App ID into workflow environment"
                               "variables sheet in Alfred Preferences"))
        self.app_id = app_id
        # Base
        currencies = load_currencies()
        base_raw = os.getenv("BASE", "USD")
        if base_raw.upper() in currencies:
            self.base = base_raw.upper()
        else:
            raise ConfigError("Invalid base currency: {}".format(base_raw),
                              ("Fix this in workflow environment"
                               "variables sheet in Alfred Preferences"))
        # Expire
        expire_raw = os.getenv("EXPIRE", 300)
        try:
            self.expire = int(expire_raw)
        except ValueError:
            raise ConfigError("Invalid expire value: {}".format(expire_raw),
                              ("Fix this in workflow environment"
                               "variables sheet in Alfred Preferences"))
        # Orientation
        orientation_raw = os.getenv("ORIENTATION", "DEFAULT").upper()
        VALID = ["DEFAULT", "FROM_FAV", "TO_FAV"]
        if orientation_raw.replace(" ", "_").upper() in VALID:
            self.orientation = orientation_raw.replace(" ", "_").upper()
        else:
            raise ConfigError(
                "Invalid orientation value: {}".format(orientation_raw),
                ("Fix this in workflow environment"
                 "variables sheet in Alfred Preferences"))
        # Precision
        precision_raw = os.getenv("PRECISION", 2)
        try:
            self.precision = int(precision_raw)
        except ValueError:
            raise ConfigError(
                "Invalid precision value: {}".format(precision_raw),
                ("Fix this in workflow environment"
                 "variables sheet in Alfred Preferences"))
