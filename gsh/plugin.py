"""
Module for declaring plugin base classes and helpers.
"""

#pylint: disable=R0921,C0301

import annex
import os

BUILTIN_PLUGIN_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "plugins")


class BaseHostLoader(object):
    """ Abstract Base Class for Writing your own host loaders.
    """

    # If you want this loaded to be available to the gsh
    # command line you can override the following attributes
    # in your plugins.
    opt_short = None
    opt_long = None
    opt_metavar = "FOO"
    opt_help = None

    def __call__(self, *args):
        """ Method called to retreive a list of hosts.

            Args:
                args: A list of keys used to generate a list of hosts.

            Returns:
                A list of hosts.
        """
        raise NotImplementedError()


class BaseExecutionHook(object):
    """ Base class for GSH Hooks.

        This class is meant to be overridden for extending GSH with your
        own hooks. The methods listed below are specified in the order in
        which they will be run.
    """

    def pre_job(self, command, hosts, timestamp):
        """ Called first before any commands are executed.

            Args:
                command: The command line that will be passed to each host.
                hosts: A list of hosts that the command will be executed on.
                timestamp: A Unix timestamp when this hook was run.
        """

    def pre_host(self, hostname, timestamp):
        """ Called for each host, before a host has started executing a command.

            Args:
                hostname: The host we're about to run a command on.
                timestamp: A Unix timestamp when this hook was run.
        """

    def update_host(self, hostname, stream, line):
        """ Called each time a new line of text has been streamed from a host.

            Args:
                hostname: The host where the output has come from.
                stream: Which output stream generated the output (stdout/stderr.)
                line: The line of output streamed from the host.
        """

    def post_host(self, hostname, return_code, timestamp):
        """ Called for each host, after a host has finished executing a command.

            Args:
                hostname: The host we're about to run a command on.
                return_code: The exitcode received from the remote command.
                timestamp: A Unix timestamp when this hook was run.
        """

    def post_job(self, timestamp):
        """ Called last after all commands have been executed.

            Args:
                timestamp: A Unix timestamp when this hook was run.
        """


def get_loaders(additional_dirs=None):
    """ Helper function to find and load all loaders. """
    if additional_dirs is None:
        additional_dirs = []
    return annex.Annex(BaseHostLoader, [
        os.path.join(BUILTIN_PLUGIN_DIR, "loaders"),
        "/etc/gsh/plugins/loaders",
        [os.path.join(plugin_dir, "loaders") for plugin_dir in additional_dirs]
    ])


def get_hooks(additional_dirs=None):
    """ Helper function to find and load all hooks. """
    if additional_dirs is None:
        additional_dirs = []
    return annex.Annex(BaseExecutionHook, [
        os.path.join(BUILTIN_PLUGIN_DIR, "hooks"),
        "/etc/gsh/plugins/hooks",
        [os.path.join(plugin_dir, "hooks") for plugin_dir in additional_dirs]
    ], instantiate=False)
