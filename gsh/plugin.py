
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


class BaseExecutionHooks(object):
    def pre_job(self):
        pass

    def post_job(self):
        pass

    def pre_host(self):
        pass

    def post_host(self):
        pass

    def update_host(self):
        pass


def get_loaders(additional_dirs=None):
    if additional_dirs is None:
        additional_dirs = []
    return annex.Annex(BaseHostLoader, BUILTIN_PLUGIN_DIR, additional_dirs)


def get_hooks(additional_dirs=None):
    if additional_dirs is None:
        additional_dirs = []
    return annex.Annex(BaseExecutionHooks, BUILTIN_PLUGIN_DIR, additional_dirs)
