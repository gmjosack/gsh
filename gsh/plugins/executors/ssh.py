import gevent
from gevent.queue import Queue, Empty
from gevent_subprocess import Popen, PIPE

from gsh.plugin import BaseExecutor, BaseInnerExecutor

class SshExecutor(BaseExecutor):
    def __init__(self, args, kwargs):
        self.ssh_opts = kwargs.get("ssh_opts", [])
        super(SshExecutor, self).__init__(args, kwargs)

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
                ["ssh", "-no", "PasswordAuthentication=no"] + self.parent.ssh_opts + [self.hostname] + self.command,
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
