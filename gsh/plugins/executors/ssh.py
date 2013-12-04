import getpass
import gevent
from gevent.pool import Pool
from gevent.queue import Queue, Empty
from gevent_subprocess import Popen, PIPE
import threading
import time

from gsh.plugin import BaseExecutor, BaseInnerExecutor

class SshExecutor(BaseExecutor):
    class Executor(BaseInnerExecutor):
        def __init__(self, *args, **kwargs):
            self.names = {}
            self._output_queue = Queue()
            super(SshExecutor.Executor, self).__init__(*args, **kwargs)

        @staticmethod
        def _stream_fd(fd, queue):
            for line in iter(fd.readline, b""):
                queue.put_nowait((fd, line))

        def _consume(self, queue):
            while True:
                try:
                    output = queue.get()
                except Empty:
                    continue

                # None is explicitly sent to shutdown the consumer
                if output is None:
                    return

                fd, line = output
                self.update(self.hostname, self.names[fd], line)

        def run(self):
            _proc = Popen(
                ["ssh", "-o", "PasswordAuthentication=no", self.hostname] + self.command,
                stdout=PIPE, stderr=PIPE
            )

            self.names = {
                _proc.stdout: "stdout",
                _proc.stderr: "stderr",
            }

            out_worker = gevent.spawn(self._stream_fd, _proc.stdout, self._output_queue)
            err_worker = gevent.spawn(self._stream_fd, _proc.stderr, self._output_queue)
            waiter = gevent.spawn(_proc.wait)
            consumer = gevent.spawn(self._consume, self._output_queue)

            gevent.joinall([out_worker, err_worker, waiter], timeout=self.timeout)

            # If we've made it here and the process hasn't completed we've timed out.
            if _proc.poll() is None:
                self._output_queue.put_nowait(
                    (_proc.stderr, "GSH: command timed out after %s second(s).\n" % self.timeout))
                _proc.kill()

            rc = _proc.wait()

            self._output_queue.put_nowait(None)
            consumer.join()

            return rc


class _PexpectThread(threading.Thread):
    def __init__(self, executor):
        self.executor = executor
        super(_PexpectThread, self).__init__()

    def run(self):
        try:
            # Defer import since most people won't want to use this executor
            # and I don't want it to be required to use gsh.
            import pxssh

            ssh = pxssh.pxssh()
            ssh.force_password = True
            ssh.login(self.executor.hostname, self.executor.parent.username, self.executor.parent.password)


            command = " ".join(self.executor.command)
            num_commands = command.count("\n") + 1
            num_prompts = 0
            ssh.sendline(command)

            # We have to block for some amount of time to wait for the data to be transfered.
            while True:
                if num_prompts >= num_commands:
                    break

                num_prompts += 1
                ssh.prompt()

                for line in ssh.before.splitlines()[1:]:
                    if not line:
                        continue
                    self.executor.update(self.executor.hostname, "stdout", line)

            ssh.logout()
        except pxssh.ExceptionPxssh, err:
            self.executor.update(self.executor.hostname, "stderr", "GSH: Failed to login: %s" % err)
            self.executor.rv = 1
            return


class PexpectExecutor(BaseExecutor):
    def __init__(self):
        super(PexpectExecutor, self).__init__()
        self.password = getpass.getpass("Password: ")
        self.username = getpass.getuser()

    class Executor(BaseInnerExecutor):
        def __init__(self, *args, **kwargs):
            super(PexpectExecutor.Executor, self).__init__(*args, **kwargs)
            self.rv = 0

        def run(self):

            thread = _PexpectThread(self)
            thread.daemon = True
            thread.start()

            sleep_duration = 0.01
            while True:
                alive = thread.is_alive()
                if not alive:
                    return self.rv
                gevent.sleep(sleep_duration)
                if sleep_duration < 0.5:
                    sleep_duration *= 2

            return self.rv

