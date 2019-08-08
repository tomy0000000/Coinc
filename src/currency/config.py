"""Helper class for loading config set in Alfred Variable Sheet"""
import os
from .utils import load_currencies

class Config():
    """Helper class for loading config set in Alfred Variable Sheet"""
    def __init__(self):
        # App_ID
        app_id = os.getenv("APP_ID")
        if not app_id:
            raise EnvironmentError(
                "Please setup APP_ID to refresh new rates",
                "Paste your App ID into workflow environment variables sheet in Alfred Preferences")
        self.app_id = app_id
        # Base
        base_raw = os.getenv("BASE")
        currencies = load_currencies()
        if not base_raw:
            self.base = "USD"
        else:
            if base_raw.upper() in currencies:
                self.base = base_raw.upper()
            else:
                raise EnvironmentError(
                    "Invalid base currency: {}".format(base_raw),
                    "Fix this in workflow environment variables sheet in Alfred Preferences")
        # Expire
        expire_raw = os.getenv("EXPIRE")
        if not expire_raw:
            self.expire = 300
        else:
            try:
                self.expire = int(expire_raw)
            except Exception:
                raise EnvironmentError(
                    "Invalid expire value: {}".format(expire_raw),
                    "Fix this in workflow environment variables sheet in Alfred Preferences")
        # Precision
        precision_raw = os.getenv("PRECISION")
        if not precision_raw:
            self.precision = 2
        else:
            try:
                self.precision = int(precision_raw)
            except Exception:
                raise EnvironmentError(
                    "Invalid precision value: {}".format(precision_raw),
                    "Fix this in workflow environment variables sheet in Alfred Preferences")
