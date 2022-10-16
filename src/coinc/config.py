"""Helper class for loading config set in Alfred Variable Sheet"""
import locale
import os

from .exceptions import ConfigError


class Config:
    """Helper class for loading config set in Alfred Environment Variables Sheet

    Raises:
        ConfigError -- Raised when there are invalid value
                       filled in Configuration Sheet
    """

    def __init__(self) -> None:
        from .utils import load_currencies

        # App_ID
        app_id = os.getenv("APP_ID")
        if not app_id:
            raise ConfigError(
                "Please setup APP_ID to refresh new rates",
                (
                    "Paste your App ID into workflow environment "
                    "variables sheet in Alfred Preferences"
                ),
            )
        self.app_id = app_id
        # Base
        currencies = load_currencies()
        base_raw = os.getenv("BASE", "USD")
        if base_raw.upper() in currencies:
            self.base = base_raw.upper()
        else:
            raise ConfigError(
                f"Invalid base currency: {base_raw}",
                (
                    "Fix this in workflow environment "
                    "variables sheet in Alfred Preferences"
                ),
            )
        # Expire
        expire_raw = os.getenv("EXPIRE", 300)
        try:
            self.expire = int(expire_raw)
        except ValueError:
            raise ConfigError(
                f"Invalid expire value: {expire_raw}",
                (
                    "Fix this in workflow environment "
                    "variables sheet in Alfred Preferences"
                ),
            )
        # Orientation
        orientation_raw = os.getenv("ORIENTATION", "DEFAULT").upper()
        VALID = ["DEFAULT", "FROM_FAV", "TO_FAV"]
        if orientation_raw.replace(" ", "_").upper() in VALID:
            self.orientation = orientation_raw.replace(" ", "_").upper()
        else:
            raise ConfigError(
                f"Invalid orientation value: {orientation_raw}",
                (
                    "Fix this in workflow environment "
                    "variables sheet in Alfred Preferences"
                ),
            )
        # Precision
        precision_raw = os.getenv("PRECISION", 2)
        try:
            self.precision = int(precision_raw)
        except ValueError:
            raise ConfigError(
                f"Invalid precision value: {precision_raw}",
                (
                    "Fix this in workflow environment "
                    "variables sheet in Alfred Preferences"
                ),
            )
        # Locale
        locale_raw = os.getenv("LOCALE", "")
        try:
            locale.setlocale(locale.LC_ALL, locale_raw)
        except locale.Error:
            raise ConfigError(
                f"Invalid locale value: {locale_raw}",
                (
                    "Fix this in workflow environment "
                    "variables sheet in Alfred Preferences"
                ),
            )
        self.locale = locale_raw
