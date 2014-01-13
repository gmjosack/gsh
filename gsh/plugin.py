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
    opt_nargs = None

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

    show_cli = True

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


class BaseExecutor(object):
    """ Base Executor to be instantiated at the job level.

        Your TopLevel Base Executor will define an inner class
        called Executor, which inherits from BaseInnerExecutor,
        which will be instantiated per host. That is where most of
        your logic will go. This outer class is for setting up
        attributes at the job level.

    Attributes:
        args: list of arguments passed through.
        kwargs: dict of keyword arguments pass through.
    """

    def __init__(self, args=None, kwargs=None):
        self.args = [] if args is None else args
        self.kwargs = {} if kwargs is None else kwargs


class BaseInnerExecutor(object):
    """ Executor to be instantiated per host.

    Attributes:
        parent: The outer, job-level, executor object.
        hostname: The hostname you'll be executing on.
        command: The command to run on the host.
        timeout: Max time before failure.
        update: A callback to write the output from the command.

    """

    def __init__(self, parent, hostname, command, timeout, update):
        self.parent = parent
        self.hostname = hostname
        self.command = command
        self.timeout = timeout
        self.update = update

    def run(self):
        """ The actual execution logic goes here.

            Returns:
                An integer, the return code of the command.
        """
        return 0


def get_loaders(additional_dirs=None):
    """ Helper function to find and load all loaders. """
    if additional_dirs is None:
        additional_dirs = []
    return annex.Annex(BaseHostLoader, [
        os.path.join(BUILTIN_PLUGIN_DIR, "loaders"),
        "/etc/gsh/plugins/loaders",
        [os.path.expanduser(os.path.join(plugin_dir, "loaders")) for plugin_dir in additional_dirs]
    ])


def get_hooks(additional_dirs=None):
    """ Helper function to find and load all hooks. """
    if additional_dirs is None:
        additional_dirs = []
    return annex.Annex(BaseExecutionHook, [
        os.path.join(BUILTIN_PLUGIN_DIR, "hooks"),
        "/etc/gsh/plugins/hooks",
        [os.path.expanduser(os.path.join(plugin_dir, "hooks")) for plugin_dir in additional_dirs]
    ], instantiate=False)


def get_executors(additional_dirs=None):
    """ Helper function to find and load all executors. """
    if additional_dirs is None:
        additional_dirs = []
    return annex.Annex(BaseExecutor, [
        os.path.join(BUILTIN_PLUGIN_DIR, "executors"),
        "/etc/gsh/plugins/executors",
        [os.path.expanduser(os.path.join(plugin_dir, "executors")) for plugin_dir in additional_dirs]
    ], instantiate=False)
