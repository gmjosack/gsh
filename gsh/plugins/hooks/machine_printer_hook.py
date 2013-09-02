
import sys
from gsh.plugin import BaseExecutionHook

class MachinePrinterHook(BaseExecutionHook):
    def update_host(self, hostname, stream, line):
        if stream not in ("stdout", "stderr"):
            return
        writer = getattr(sys, stream)
        writer.write("%s: %s" % (hostname, line))


