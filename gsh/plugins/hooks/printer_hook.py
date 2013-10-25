
import sys
from gsh.plugin import BaseExecutionHook


class PrinterHook(BaseExecutionHook):
    def __init__(self, *args, **kwargs):
        self.prepend_host = False
        self.longest_len = 0
        super(PrinterHook, self).__init__(*args, **kwargs)

    def pre_job(self, command, hosts, timestamp):
        # Add one to account for :
        self.longest_len = len(max(hosts, key=len)) + 1

    def update_host(self, hostname, stream, line):
        if stream not in ("stdout", "stderr"):
            return
        writer = getattr(sys, stream)
        line = line.decode('utf-8')

        try:
            self._write(writer, hostname, line)
        except IOError as err:
            if writer is not sys.stderr:
                output = "Failed to write to stream %s: (%s, %s)\n" % (stream, err.errno, err.strerror)
                self._write(sys.stderr, hostname, output)

    def _write(self, stream, hostname, line):
        if self.prepend_host:
            line = "%%-%ss %%s" % self.longest_len % (hostname + ":", line)
        stream.write(line)
        stream.flush()



class MachinePrinterHook(PrinterHook):
    def __init__(self, *args, **kwargs):
        self.prepend_host = True
        super(PrinterHook, self).__init__(*args, **kwargs)
