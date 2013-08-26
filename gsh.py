#!/usr/bin/env python

import sys

import gevent
from gevent.pool import Pool
from gevent.queue import Queue, Empty

from subprocess import Popen, PIPE


def remote_command(hostname, command, output_callbacks=None):
    proc = Popen(["ssh", hostname] + command, stdout=PIPE, stderr=PIPE, bufsize=1)

    names = {
        proc.stdout: "stdout",
        proc.stderr: "stderr",
    }

    output_queue = Queue()

    def stream_fd(fd, queue):
        for line in iter(fd.readline, b""):
            queue.put_nowait((fd, line))

    def consume(queue):
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


    out_ev = gevent.spawn(stream_fd, proc.stdout, output_queue)
    err_ev = gevent.spawn(stream_fd, proc.stderr, output_queue)
    consumer = gevent.spawn(consume, output_queue)

    gevent.joinall([out_ev, err_ev])
    output_queue.put_nowait(None)
    consumer.join()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run a command across many machines.")
    parser.add_argument("command", nargs="*", default=None, help="Command to execute remotely.")
    parser.add_argument("-f", "--file", default=[], action="append", help="Use the file as list of machines.")
    parser.add_argument("-F", "--forklimit", default=64, type=int, help="Limit on concurrenct processes.")
    args = parser.parse_args()

    hosts = []
    for host_file in args.file:
        hosts.extend([line.strip() for line in open(host_file)])

    if not args.command or not any(args.command):
        print "\n".join(hosts)
        sys.exit()


    greenlets = []
    try:
            gsh_pool = Pool(args.forklimit)

            for host in hosts:
                greenlets.append(gsh_pool.apply_async(remote_command, (host, args.command)))
            gevent.joinall(greenlets)
            gsh_pool.join()
    except KeyboardInterrupt:
        sys.exit("Bye")


if __name__ == "__main__":
    main()
