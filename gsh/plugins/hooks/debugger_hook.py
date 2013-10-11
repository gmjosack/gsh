
import sys
from gsh.plugin import BaseExecutionHook

class DebuggerHook(BaseExecutionHook):
    def update_host(self, hostname, stream, line):
        print "Running update_host hook: ", (hostname, stream, line)

    def pre_host(self, *args):
        print "Running pre_host hook:", args

    def post_host(self, *args):
        print "Running post_host hook:", args

    def pre_job(self, *args):
        print "Running pre_job hook:", args

    def post_job(self, *args):
        print "Running post_job hook:", args
