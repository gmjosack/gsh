
import logging

from gsh.plugin import BaseHostLoader

class FileLoader(BaseHostLoader):
    opt_short = "-f"
    opt_long = "--file"
    opt_metavar = "FILE"
    opt_help = "Get a list of machines from the specified file."

    def __call__(self, *args):
        hosts = []
        for host_file in args:
            hosts.extend([line.strip() for line in open(host_file)])
        return hosts

