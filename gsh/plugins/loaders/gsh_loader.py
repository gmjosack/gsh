
import os
import re

from gsh.plugin import BaseHostLoader
from gsh.exceptions import LoaderError


# These locations will be iterated over using the first
# match to pull hosts from. dsh locations are searched
# to make transition from dsh to gsh more seemless.
GROUP_FILE_LOCATIONS = (
    "~/.gsh/group",
    "~/.dsh/group",
    "/etc/gsh/group",
    "/etc/dsh/group",
)

VALID_GROUPNAME = re.compile(r"^[\w\-=]*$")


class GshLoader(BaseHostLoader):
    opt_short = "-g"
    opt_long = "--group"
    opt_metavar = "GROUP"
    opt_help = "Get a list of machines from a GSH/DSH Group."

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

            if not VALID_GROUPNAME.match(group):
                raise LoaderError("Invalid group name: %s" % group)

            group_found = False

            for location in GROUP_FILE_LOCATIONS:
                group_filename = os.path.join(os.path.expanduser(location), group)

                if not os.path.isfile(group_filename):
                    continue

                group_found = True
                hosts.update(_read_group_file(group_filename))
                break  # We only want the first match. Stop iteration if we get here.

            if not group_found:
                raise LoaderError("Failed to find group file for: %s" % group)

        return hosts


def _read_group_file(group_filename):
    hosts = set()
    with open(group_filename) as group_file:
        for line in group_file:
            line = line.strip()
            line = line.split("#")[0]
            if not line:
                continue
            hosts.add(line)
    return hosts
