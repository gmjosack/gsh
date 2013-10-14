from gsh.plugin import BaseExecutionHook

class BufferedOutputHook(BaseExecutionHook):
    """ Hook to capture output from a RemotePopen call."""
    def __init__(self):
        self.stdout = []
        self.stderr = []
        self.rc = None

    def update_host(self, hostname, stream, line):
        if stream not in ("stdout", "stderr"):
            return
        getattr(self, stream).append(line)

    def post_host(self, hostname, rc, timestamp):
        self.rc = rc


class MultiBufferedOutputHook(BaseExecutionHook):
    """ Hook to gather output from all hosts on a Gsh call."""
    def __init__(self):
        self.hosts = {}

    def pre_host(self, hostname, timestamp):
        self.hosts[hostname] = BufferedOutputHook()

    def update_host(self, hostname, *args, **kwargs):
        self.hosts[hostname].update_host(hostname, *args, **kwargs)

    def post_host(self, hostname, *args, **kwargs):
        self.hosts[hostname].post_host(hostname, *args, **kwargs)


