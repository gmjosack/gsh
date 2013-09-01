

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

    def run(self, *args):
        raise NotImplementedError()

