#!/usr/bin/env python

import os
import yaml

from .exceptions import ConfigError


class Config(object):

    def __init__(self):
        self.forklimit = 64
        self.print_machines = True
        self.concurrent = True
        self.timeout = 0
        self.plugin_dirs = set()
        self.hooks = set()

    def __repr__(self):
        return (
            "Config(forklimit=%r, print_machines=%r, concurrent=%r, "
            "timeout=%r, plugin_dirs=%r, hooks=%r)"
        ) % (
            self.forklimit, self.print_machines, self.concurrent,
            self.timeout, self.plugin_dirs, self.hooks
        )

    def update_from_file(self, config):
        try:
            with open(config) as config_file:
                data = yaml.safe_load(config_file)
                if not isinstance(data, dict):
                    data = {}

            self.forklimit = data.get("forklimit", self.forklimit)
            self.print_machines = data.get("print_machines", self.print_machines)
            self.concurrent = data.get("concurrent", self.concurrent)
            self.timeout = data.get("timeout", self.timeout)

            plugin_dirs = data.get("plugin_dirs", [])
            if isinstance(plugin_dirs, basestring):
                plugin_dirs = [plugin_dirs]
            self.plugin_dirs.update(plugin_dirs)

            hooks = data.get("hooks", [])
            if isinstance(hooks, basestring):
                hooks = [hooks]
            self.hooks.update(hooks)

        # It's okay to ignore files that don't exist.
        except IOError:
            pass
        except (yaml.parser.ParserError, yaml.scanner.ScannerError) as err:
            raise ConfigError("Invalid Configuration (%s): %s" % (config, err.problem))

    def update_from_args(self, args):

        self.plugin_dirs.update(args.plugin_dirs)
        self.hooks.update(getattr(args, "hooks", []))

        if getattr(args, "forklimit", None) is not None:
            self.forklimit = args.forklimit
        if getattr(args, "print_machines", None) is not None:
            self.print_machines = args.print_machines
        if getattr(args, "concurrent", None) is not None:
            self.concurrent = args.concurrent
        if getattr(args, "timeout", None) is not None:
            self.timeout = args.timeout

    def load_default_files(self):
        self.update_from_file("/etc/gsh/gsh.yaml")
        self.update_from_file(os.path.expanduser("~/.gsh/gsh.yaml"))
