
import gevent
from gevent.pool import Pool
from gevent.queue import Queue, Empty
from gevent_subprocess import Popen, PIPE
import time


class RemotePopen(object):

    QUEUED = 0
    RUNNING = 1
    FAILED = 2
    SUCCESS = 3

    def __init__(self, hostname, command, timeout=None, hooks=None):
        self.hostname = hostname
        self.command = command
        self.timeout = timeout

        # Treat 0 second timeouts as no timeout.
        if not timeout:
            self.timeout = None

        if hooks is None:
            hooks = []
        self.hooks = hooks

        self.status = RemotePopen.QUEUED
        self.rc = None

        self._output_queue = Queue()
        self._proc = None

        self._pre_host_hooks = None
        self._post_host_hooks = None

    def _run_pre_host_hooks(self):
        for hook in self.hooks:
            hook.pre_host(self.hostname, time.time())

    def _run_post_host_hooks(self):
        for hook in self.hooks:
            hook.post_host(self.hostname, self.rc, time.time())

    @staticmethod
    def _stream_fd(fd, queue):
        for line in iter(fd.readline, b""):
            queue.put_nowait((fd, line))

    def _consume(self, queue, hostname, names):
        while True:
            try:
                output = queue.get()
            except Empty:
                continue

            # None is explicitly sent to shutdown the consumer
            if output is None:
                return

            fd, line = output
            for hook in self.hooks:
                hook.update_host(hostname, names[fd], line)

    def run(self):
        self._pre_host_hooks = gevent.spawn(self._run_pre_host_hooks)
        self._pre_host_hooks.join()

        self.status = RemotePopen.RUNNING
        self._proc = Popen(["ssh", "-o", "PasswordAuthentication=no", self.hostname] + self.command, stdout=PIPE, stderr=PIPE)

        names = {
            self._proc.stdout: "stdout",
            self._proc.stderr: "stderr",
        }

        out_worker = gevent.spawn(self._stream_fd, self._proc.stdout, self._output_queue)
        err_worker = gevent.spawn(self._stream_fd, self._proc.stderr, self._output_queue)
        waiter = gevent.spawn(self._proc.wait)
        consumer = gevent.spawn(self._consume, self._output_queue, self.hostname, names)

        gevent.joinall([out_worker, err_worker, waiter], timeout=self.timeout)

        # If we've made it here and the process hasn't completed we've timed out.
        if self._proc.poll() is None:
            self._output_queue.put_nowait(
                (self._proc.stderr, "GSH: command timed out after %s second(s).\n" % self.timeout))
            self._proc.kill()

        self.rc = self._proc.wait()

        if not self.rc:
            self.status = RemotePopen.SUCCESS
        else:
            self.status = RemotePopen.FAILED

        self._post_host_hooks = gevent.spawn(self._run_post_host_hooks)
        self._post_host_hooks.join()

        self._output_queue.put_nowait(None)
        consumer.join()


class Gsh(object):
    def __init__(self, hosts, command, fork_limit=1, timeout=None, hooks=None):
        self.hosts = set(hosts)
        self.command = command
        self.fork_limit = self._build_fork_limit(fork_limit, len(self.hosts))
        self.timeout = timeout

        # Treat 0 second timeouts as no timeout.
        if not timeout:
            self.timeout = None

        if hooks is None:
            hooks = []
        self.hooks = hooks

        self._pool = Pool(max(self.fork_limit, 1))
        self._greenlets = []
        self._remotes = []

        self._pre_job_hooks = None
        self._post_job_hooks = None

    @staticmethod
    def _build_fork_limit(fork_limit, num_hosts):
        if isinstance(fork_limit, int) or fork_limit.isdigit():
            return int(fork_limit)
        if fork_limit.endswith("%"):
            return int(float(num_hosts) * (float(fork_limit[:-1]) / 100.0))
        # If we can't parse your forklimit go serial for safety.
        return 1

    def run_async(self):

        # Don't start executing until the pre_job hooks have completed.
        self._pre_job_hooks = gevent.spawn(self._run_pre_job_hooks)
        self._pre_job_hooks.join()

        for host in self.hosts:
            remote_command = RemotePopen(host, self.command, hooks=self.hooks, timeout=self.timeout)
            self._remotes.append(remote_command)
            self._greenlets.append(self._pool.apply_async(remote_command.run))

        self._post_job_hooks = gevent.spawn(self._run_post_job_hooks)

    def _run_pre_job_hooks(self):
        for hook in self.hooks:
            hook.pre_job(self.command, self.hosts, time.time())

    def _run_post_job_hooks(self):
        # Wait for all greenlets to finish before running these hooks.
        gevent.joinall(self._greenlets)
        for hook in self.hooks:
            hook.post_job(time.time())

    def wait(self, timeout=None):
        rc = 0
        gevent.joinall(self._greenlets + [self._post_job_hooks], timeout=timeout, raise_error=True)
        for remote in self._remotes:
            if remote.rc:
                return remote.rc
        return rc
