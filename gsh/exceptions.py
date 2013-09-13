
class Error(Exception):
    """ Base Error for all gsh exceptions."""


class ConfigError(Error):
    """ Error parsing configuration."""
