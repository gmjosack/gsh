from core import Gsh
from plugin import get_hooks

def run_remote_command(hosts, command, fork_limit=64, timeout=None):
    hooks = get_hooks()
    buffered_output = hooks.MultiBufferedOutputHook()

    procs = Gsh(
        hosts=hosts,
        command=command,
        fork_limit=fork_limit,
        timeout=timeout,
        hooks=[buffered_output])

    procs.run_async()
    procs.wait()

    return buffered_output.hosts
