"""Exceptions used in this module"""


class CoonError(Exception):
    """Base Class used to declare other errors for Coon

    Extends:
        Exception
    """
    pass


class ConfigError(CoonError):
    """Raised when there are invalid value filled in Configuration Sheet

    Extends:
        CoonError
    """
    pass


class QueryError(CoonError):
    """Raised when invalid query were given

    Extends:
        CoonError
    """
    pass


class AppIDError(CoonError):
    """Raised when App ID can not be used

    Extends:
        CoonError
    """
    pass


class ApiError(CoonError):
    """Raised when API is unreachable or return bad response

    Extends:
        CoonError
    """
    pass


class UnknownPythonError(CoonError):
    """Raised when Python runtime version can not be correctly detacted

    Extends:
        CoonError
    """
    pass
