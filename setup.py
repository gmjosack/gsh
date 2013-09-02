#!/usr/bin/env python

from distutils.core import setup

kwargs = {
    "name": "gsh",
    "version": "0.1",
    "packages": ["gsh"],
    "package_data": {"gsh": ["plugins/loaders/*.py", "plugins/hooks/*.py"]},
    "scripts": ["bin/gsh"],
    "description": "Pluggable Distributed SSH Command Executer.",
    "author": "Gary M. Josack",
    "maintainer": "Gary M. Josack",
    "author_email": "gary@byoteki.com",
    "maintainer_email": "gary@byoteki.com",
    # "license": "",
    "url": "https://github.com/gmjosack/gsh",
    "download_url": "https://github.com/gmjosack/gsh/archive/master.tar.gz",
    "classifiers": [
        "Programming Language :: Python",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
}

setup(**kwargs)
