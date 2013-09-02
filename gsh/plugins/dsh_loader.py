
import os

from gsh.plugin import BaseHostLoader

class DshLoader(BaseHostLoader):
    opt_short = "-g"
    opt_long = "--group"
    opt_metavar = "GROUP"
    opt_help = "Get a list of machines from a DSH Group."

    def __call__(self, *args):
        hosts = set()
        groups = set()

        for group in args:
            group = group.replace(" ", "").strip()
            if "," in group:
                groups.update(group.split(","))
            else:
                groups.add(group)

        for group in groups:
            with open(os.path.join("/etc/dsh/group", group)) as group_file:
                for line in group_file:
                    line = line.strip()
                    line = line.split("#")[0]
                    if not line:
                        continue
                    hosts.add(line)

        return hosts

