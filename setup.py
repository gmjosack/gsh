#!/usr/bin/env python

from distutils.core import setup

execfile('gsh/version.py')

with open('requirements.txt') as requirements:
    required = requirements.read().splitlines()

kwargs = {
    "name": "gsh",
    "version": str(__version__),
    "packages": ["gsh"],
    "package_data": {"gsh": ["plugins/loaders/*.py", "plugins/hooks/*.py"]},
    "scripts": ["bin/gsh"],
    "description": "Pluggable Distributed SSH Command Executer.",
    # PyPi, despite not parsing markdown, will prefer the README.md to the
    # standard README. Explicitly read it here.
    "long_description": open("README").read(),
    "author": "Gary M. Josack",
    "maintainer": "Gary M. Josack",
    "author_email": "gary@byoteki.com",
    "maintainer_email": "gary@byoteki.com",
    "license": "MIT",
    "install_requires": required,
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
