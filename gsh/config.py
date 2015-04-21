""" Configuation related objects and helpers."""

import os
import yaml

from .exceptions import ConfigError


class Config(object):
    """ Configuration object for GSH.

    This object is used as the canonical source for options in GSH. This
    allows for easily setting defaults and having them overridden from
    multiple sources, such as configuration files, arguments on the command
    line and potentially environment variables. This is mostly used for the
    the command line utility.

    Attributes:
        forklimit: The number of concurrent processes to fork at a time.
        print_machines: Whether to prefix output with machine names.
        print_output: Whether to print output from the executed commands.
        show_percent: Whether to prefix output with percentage of completion.
        concurrent: Whether to perform operation sequentially vs concurrently.
        timeout: How long to wait for a command to finish on a host.
        plugin_dirs: Where to look for addition plugins.
        hooks: Which hooks to pass through to Gsh.
        executor: Which executor to run the commands with.

    """

    def __init__(self):
        self.forklimit = 64
        self.print_machines = True
        self.print_output = True
        self.show_percent = False
        self.concurrent = True
        self.timeout = 0
        self.plugin_dirs = set()
        self.hooks = set()
        self.executor = "ssh"
        self.executor_args = []
        self.executor_kwargs = {}

    def __repr__(self):
        return (
            "Config(forklimit=%r, print_machines=%r, print_output=%r, show_percent=%r, "
            "concurrent=%r, timeout=%r, plugin_dirs=%r, hooks=%r, executor=%r)"
        ) % (
            self.forklimit, self.print_machines, self.print_output, self.show_percent,
            self.concurrent, self.timeout, self.plugin_dirs, self.hooks, self.executor,
        )

    def update_from_file(self, config):
        """ Updates the configuration attributes from a file."""
        try:
            with open(config) as config_file:
                data = yaml.safe_load(config_file)
                if not isinstance(data, dict):
                    data = {}

            self.forklimit = data.get("forklimit", self.forklimit)
            self.print_machines = data.get("print_machines", self.print_machines)
            self.print_output = data.get("print_output", self.print_output)
            self.show_percent = data.get("show_percent", self.show_percent)
            self.concurrent = data.get("concurrent", self.concurrent)
            self.timeout = data.get("timeout", self.timeout)

            self._parse_executor(data.get("executor", self.executor))

            plugin_dirs = data.get("plugin_dirs", [])
            if isinstance(plugin_dirs, basestring):
                plugin_dirs = [plugin_dirs]
            self.plugin_dirs.update(plugin_dirs)

            self._parse_hooks(data.get("hooks", []))

        # It's okay to ignore files that don't exist.
        except IOError:
            pass
        except (yaml.parser.ParserError, yaml.scanner.ScannerError) as err:
            raise ConfigError(
                "Invalid Configuration (%s): %s" % (config, err.problem))

    def _parse_executor(self, executor):
        """ Parses an executor string of the form ssh:arg1,arg2,kwarg1=foo. """

        arguments = ""
        args = []
        kwargs = {}

        if ":" in executor:
            executor, arguments = executor.split(":", 1)

        for argument in arguments.split(","):
            argument = argument.strip()

            if "=" in argument:
                key, value = argument.split("=", 1)
                key = key.strip()
                value = value.strip()
                kwargs[key] = value
            else:
                args.append(argument)

        self.executor, self.executor_args, self.executor_kwargs = executor, args, kwargs

    def _parse_hooks(self, hooks):
        if isinstance(hooks, basestring):
            hooks = [hooks]

        hooks = set([subhook for hook in hooks for subhook in hook.split(",")])

        for hook in hooks:
            hook = hook.strip()
            if not hook:
                continue
            if hook[0] == "-":
                if hook[1:] in self.hooks:
                    self.hooks.remove(hook[1:])
            else:
                self.hooks.add(hook)

    def update_from_args(self, args):
        """ Update config object from an argparse args object."""

        self.plugin_dirs.update(args.plugin_dirs)
        self._parse_hooks(getattr(args, "hooks", []))

        if getattr(args, "forklimit", None) is not None:
            self.forklimit = args.forklimit
        if getattr(args, "print_machines", None) is not None:
            self.print_machines = args.print_machines
        if getattr(args, "print_output", None) is not None:
            self.print_output = args.print_output
        if getattr(args, "show_percent", None) is not None:
            self.show_percent = args.show_percent
        if getattr(args, "concurrent", None) is not None:
            self.concurrent = args.concurrent
        if getattr(args, "timeout", None) is not None:
            self.timeout = args.timeout
        if getattr(args, "executor", None) is not None:
            self._parse_executor(args.executor)
        if getattr(args, "remoteshellopt", []):
            self.executor_kwargs["ssh_opts"] = args.remoteshellopt

    def load_default_files(self):
        """ Update config object from standard config file locations."""
        self.update_from_file("/etc/gsh/gsh.yaml")
        self.update_from_file(os.path.expanduser("~/.gsh/gsh.yaml"))
