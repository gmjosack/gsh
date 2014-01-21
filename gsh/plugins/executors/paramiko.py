import cStringIO
import getpass
import gevent
import select
import socket
import termios
import threading
import tty

from gsh.plugin import BaseExecutor, BaseInnerExecutor


class _ParamikoThread(threading.Thread):
    def __init__(self, executor):
        self.executor = executor
        super(_ParamikoThread, self).__init__()

    def interactive(self, ssh, command):
        stdout = cStringIO.StringIO()
        stderr = cStringIO.StringIO()
        chan = ssh.invoke_shell()

        for cmd in command.split("\n"):
            cmd = cmd.strip()
            if not cmd:
                continue
            chan.send(cmd + "\n")

        while True:
            read, write, error = select.select([chan], [], [], 5)

            if not any([read, write, error]):
                stderr.write("GSH: Channel Timed Out!\n")
                break

            if chan in read:
                try:
                    out = chan.recv(1024)
                    if not out:
                        break
                    stdout.write(out)
                except socket.timeout:
                    pass

        chan.close()
        stdout.seek(0)
        stderr.seek(0)
        return stdout, stderr


    def run(self):
        # Defer import since most people won't want to use this executor
        # and I don't want it to be required to use gsh.
        import paramiko

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            try:
                ssh.connect(self.executor.hostname, password=self.executor.parent.password, timeout=5)
            except socket.timeout, err:
                self.executor.update(self.executor.hostname, "stderr", "GSH: Connection timeout: %s" % err)
                self.executor.rv = 1
                return

            command = " ".join(self.executor.command)

            if "interactive" in self.executor.parent.args:
                stdout, stderr = self.interactive(ssh, command)
                rv = 0  # Find a way to get rv later.
            else:
                stdin, stdout, stderr = ssh.exec_command(command)
                rv = stdout.channel.recv_exit_status()

            for line in stdout.read().splitlines():
                self.executor.update(self.executor.hostname, "stdout", line)

            for line in stderr.read().splitlines():
                self.executor.update(self.executor.hostname, "stderr", line)

            ssh.close()
            self.executor.rv = rv
        except paramiko.BadAuthenticationType, err:
            self.executor.update(self.executor.hostname, "stderr", "GSH: Failed to login.")
            self.executor.rv = 1


class ParamikoExecutor(BaseExecutor):
    def __init__(self, args, kwargs):

        # This import is unused but I want it to blow up
        # at the job level if it's not found
        import paramiko

        super(ParamikoExecutor, self).__init__(args, kwargs)
        if "password" in kwargs:
            self.password = kwargs["password"]
        else:
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
