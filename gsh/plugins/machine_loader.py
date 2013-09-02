
import logging

from gsh.plugin import BaseHostLoader

class MachineLoader(BaseHostLoader):
    opt_short = "-m"
    opt_long = "--machine"
    opt_metavar = "HOST"
    opt_help = "Execute on the specified machine."

    def __call__(self, *args):
        hosts = []
        for machine in args:
            machine = machine.replace(" ", "")
            if "," in machine:
                hosts.extend(machine.split(","))
            else:
                hosts.append(machine)
        return hosts

