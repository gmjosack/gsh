""" Exception related objects and helpers."""

class Error(Exception):
    """ Base Error for all gsh exceptions."""


class ConfigError(Error):
    """ Error parsing configuration."""

class LoaderError(Error):
    """ Error loading hosts from loader plugin."""
