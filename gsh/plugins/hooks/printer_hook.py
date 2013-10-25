
import sys
from gsh.plugin import BaseExecutionHook

def update_host_handler(hostname, stream, line, prepend_host=False):
        if stream not in ("stdout", "stderr"):
            return
        writer = getattr(sys, stream)
        line = line.decode('utf-8')
        if prepend_host:
            line = "%s: %s" % (hostname, line)
        try:
            writer.write(line)
            writer.flush()
        except IOError as err:
            if writer is not sys.stderr:
                output = "Failed to write to stream %s: (%s, %s)\n" % (stream, err.errno, err.strerror)
                if prepend_host:
                    output = "%s: %s" % (hostname, output)
                sys.stderr.write(output)


class PrinterHook(BaseExecutionHook):
    def update_host(self, hostname, stream, line):
        return update_host_handler(hostname, stream, line)


class MachinePrinterHook(BaseExecutionHook):
    def update_host(self, hostname, stream, line):
        return update_host_handler(hostname, stream, line, prepend_host=True)


