
import annex
import os

BUILTIN_PLUGIN_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "plugins")


class BaseHostLoader(object):
    """ Abstract Base Class for Writing your own host loaders.
    """

    # If you want this loaded to be available to the gsh
    # command line you can override the following attributes
    # in your plugins.
    opt_short = None
    opt_long = None
    opt_metavar = "FOO"
    opt_help = None

    def __call__(self, *args):
        raise NotImplementedError()


class BaseExecutionHook(object):
    def pre_job(self, command, hosts, ts):
        pass

    def post_job(self, ts):
        pass

    def pre_host(self):
        pass

    def post_host(self):
        pass

    def update_host(self, hostname, stream, line):
        pass


def get_loaders(additional_dirs=None):
    if additional_dirs is None:
        additional_dirs = []
    return annex.Annex(BaseHostLoader,
                       os.path.join(BUILTIN_PLUGIN_DIR, "loaders"),
                       "/etc/gsh/plugins/loaders",
                       *[os.path.join(plugin_dir, "loaders") for plugin_dir in additional_dirs])


def get_hooks(additional_dirs=None):
    if additional_dirs is None:
        additional_dirs = []
    return annex.Annex(BaseExecutionHook,
                       os.path.join(BUILTIN_PLUGIN_DIR, "hooks"),
                       "/etc/gsh/plugins/hooks",
                       *[os.path.join(plugin_dir, "hooks") for plugin_dir in additional_dirs])
