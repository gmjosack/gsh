#!/usr/bin/env python

import pipes
import sys

import gevent
from gevent.select import select, error as select_error
from gevent.pool import Pool

try:
    from gevent.subprocess import Popen, PIPE
    # gevent.subprocess only exists in gevent-1.0 which isn't
    # available on PyPI yet. Fall back to gevent_subprocess
    # if it's not available.
except ImportError:
    try:
        from gevent_subprocess import Popen, PIPE
        # If this library isn't installed either just fall back to
        # the stdlib subprocess module. It'll be slower but still
        # work fairly well.
    except ImportError:
        from subprocess import Popen, PIPE


def quote_for_ssh(args):
    return " ".join(pipes.quote(s) for s in args)


def remote_command(hostname, command, output_callbacks=None):
    proc = Popen(["ssh", hostname] + command, stdout=PIPE, stderr=PIPE)

    output_fds = {
        proc.stdout: dict(name="stdout", finished=False),
        proc.stderr: dict(name="stderr", finished=False),
    }

    while not all([output_fds[proc.stdout]["finished"],
                   output_fds[proc.stdout]["finished"]]):
        read_fds = [key for key, val in output_fds.iteritems() if not val["finished"]]
        read_fds = select(read_fds, [], [], .2)[0]
        for read_fd in read_fds:
            output = read_fd.readline()
            if not output:
                output_fds[read_fd]["finished"] = True
            if output:
                #print hostname, output_fds[read_fd]["name"], output,
                print "%s: %s" % (hostname, output)

        if proc.poll() is not None:
            print hostname, "finished"
            break
        print hostname, "next run"

    return



def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run a command across many machines.")
    parser.add_argument("command", nargs="*", default=None, help="Command to execute remotely.")
    parser.add_argument("-F", "--forklimit", default=64, type=int, help="Limit on concurrenct processes.")
    args = parser.parse_args()

    hosts = [line.strip() for line in open("hosts")]

    if not args.command or not any(args.command):
        print "\n".join(hosts)
        sys.exit()

    try:
        if args.forklimit == 1:
            for host in hosts:
                remote_command(host, args.command)
        else:
            gsh_pool = Pool(args.forklimit)

            for host in hosts:
                gsh_pool.apply_async(remote_command, (host, args.command))

            gsh_pool.join()
    except KeyboardInterrupt:
        sys.exit("Bye")


if __name__ == "__main__":
    main()
