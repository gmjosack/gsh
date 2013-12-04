import getpass
import gevent
import threading

from gsh.plugin import BaseExecutor, BaseInnerExecutor


class _ParamikoThread(threading.Thread):
    def __init__(self, executor):
        self.executor = executor
        super(_ParamikoThread, self).__init__()

    def run(self):
        # Defer import since most people won't want to use this executor
        # and I don't want it to be required to use gsh.
        import paramiko

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.executor.hostname, password=self.executor.parent.password)

            command = " ".join(self.executor.command)
            stdin, stdout, stderr = ssh.exec_command(command)


            for line in stdout.read().splitlines():
                self.executor.update(self.executor.hostname, "stdout", line)

            for line in stderr.read().splitlines():
                self.executor.update(self.executor.hostname, "stderr", line)

            ssh.close()
            self.executor.rv = stdout.channel.recv_exit_status()
        except paramiko.BadAuthenticationType, err:
            self.executor.update(self.executor.hostname, "stderr", "GSH: Failed to login.")
            self.executor.rv = 1


class ParamikoExecutor(BaseExecutor):
    def __init__(self):

        # This import is unused but I want it to blow up
        # at the job level if it's not found
        import paramiko

        super(ParamikoExecutor, self).__init__()
        self.password = getpass.getpass("Password: ")
        self.username = getpass.getuser()

    class Executor(BaseInnerExecutor):
        def __init__(self, *args, **kwargs):
            super(ParamikoExecutor.Executor, self).__init__(*args, **kwargs)
            self.rv = 0

        def run(self):

            thread = _ParamikoThread(self)
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
