#!/usr/bin/env python

import sys

import gevent
from gevent.pool import Pool
from gevent.queue import Queue, Empty

from gevent_subprocess import Popen, PIPE

class Error(Exception):
    pass

class RemotePopen(object):

    QUEUED = 0
    RUNNING = 1
    FAILED = 2
    SUCCESS = 3

    def __init__(self, hostname, command, timeout=None):
        self.hostname = hostname
        self.command = command
        self.timeout = timeout

        self.status = RemotePopen.QUEUED
        self.rc = None

        self._output_queue = Queue()
        self._proc = None

    @staticmethod
    def stream_fd(fd, queue):
        for line in iter(fd.readline, b""):
            queue.put_nowait((fd, line))

    @staticmethod
    def consume(queue, hostname, names):
        while True:
            try:
                output = queue.get()
            except Empty:
                continue

            # None is explicitly sent to shutdown the consumer
            if output is None:
                return

            fd, line = output
            print "%s(%s): %s" % (hostname, names[fd], line),

    def run(self):
        self.status = RemotePopen.RUNNING
        self._proc = Popen(["ssh", self.hostname] + self.command, stdout=PIPE, stderr=PIPE)

        names = {
            self._proc.stdout: "stdout",
            self._proc.stderr: "stderr",
        }

        out_worker = gevent.spawn(self.stream_fd, self._proc.stdout, self._output_queue)
        err_worker = gevent.spawn(self.stream_fd, self._proc.stderr, self._output_queue)
        consumer = gevent.spawn(self.consume, self._output_queue, self.hostname, names)

        gevent.joinall([out_worker, err_worker])
        self._output_queue.put_nowait(None)
        consumer.join()
        self.rc = self._proc.wait()


class Gsh(object):
    def __init__(self, hosts, command, fork_limit=1, timeout=None):
        self.hosts = set(hosts)
        self.command = command
        self.fork_limit = fork_limit
        self.timeout = timeout

        self._pool = Pool(max(self.fork_limit, 1))
        self._greenlets = []
        self._remotes = []

    def run_async(self):
        for host in self.hosts:
            remote_command = RemotePopen(host, self.command)
            self._remotes.append(remote_command)
            self._greenlets.append(self._pool.apply_async(remote_command.run))

    def wait(self, timeout=None):
        rc = 0
        gevent.joinall(self._greenlets, timeout=timeout, raise_error=True)
        for remote in self._remotes:
            if remote.rc:
                return remote.rc
        return rc


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run a command across many machines.")
    parser.add_argument("command", nargs="*", default=None, help="Command to execute remotely.")
    parser.add_argument("-f", "--file", default=[], action="append", help="Use the file as list of machines.")
    parser.add_argument("-t", "--timeout", default=0, type=int, help="How long to allow a command to run before timeout.")
    parser.add_argument("-F", "--forklimit", default=64, type=int, help="Limit on concurrenct processes.")
    args = parser.parse_args()

    hosts = []
    for host_file in args.file:
        hosts.extend([line.strip() for line in open(host_file)])

    if not args.command or not any(args.command):
        print "\n".join(hosts)
        sys.exit()

    try:
        gsh = Gsh(hosts, args.command, fork_limit=args.forklimit, timeout=args.timeout)
        gsh.run_async()
        sys.exit(gsh.wait())
    except KeyboardInterrupt:
        sys.exit("Bye")


if __name__ == "__main__":
    main()
