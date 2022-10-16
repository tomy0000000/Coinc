"""Exceptions used in this module"""


class CoincError(Exception):
    """Base Class used to declare other errors for Coinc

    Extends:
        Exception
    """

    pass


class ConfigError(CoincError):
    """Raised when there are invalid value filled in Configuration Sheet

    Extends:
        CoincError
    """

    pass


class QueryError(CoincError):
    """Raised when invalid query were given

    Extends:
        CoincError
    """

    pass


class AppIDError(CoincError):
    """Raised when App ID can not be used

    Extends:
        CoincError
    """

    pass


class ApiError(CoincError):
    """Raised when API is unreachable or return bad response

    Extends:
        CoincError
    """

    pass
