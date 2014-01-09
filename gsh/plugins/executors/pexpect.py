import getpass
import gevent
import threading

from gsh.plugin import BaseExecutor, BaseInnerExecutor


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
    def __init__(self, args, kwargs):
        # This import is unused but I want it to blow up
        # at the job level if it's not found
        import pxssh

        super(PexpectExecutor, self).__init__(args, kwargs)
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

