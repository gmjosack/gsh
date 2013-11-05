
import sys
import math
from gsh.plugin import BaseExecutionHook


class PrinterHook(BaseExecutionHook):
    def __init__(self, *args, **kwargs):
        self.prepend_host = kwargs.pop("prepend_host", True)
        self.show_percent = kwargs.pop("show_percent", False)
        self.add_newline = kwargs.pop("add_newline", True)

        self.hosts_total = 0
        self.hosts_finished = 0
        self.hosts_percent = 0
        self.longest_len = 0

        super(PrinterHook, self).__init__(*args, **kwargs)

    def pre_job(self, command, hosts, timestamp):
        self.hosts_total = len(hosts)
        if hosts:
            # Add one to account for colons
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

    def post_host(self, hostname, return_code, timestamp):
        self.hosts_finished += 1
        self.hosts_percent = int(math.ceil(float(self.hosts_finished) * 100 / self.hosts_total))

    def _write(self, stream, hostname, line):
        if self.prepend_host:
            line = "%%-%ss %%s" % self.longest_len % (hostname + ":", line)

        if self.show_percent:
            line = "(%3s%%) %s" % (self.hosts_percent, line)

        if self.add_newline and line and line[-1] != "\n":
            line += "\n"

        stream.write(line)
        stream.flush()
