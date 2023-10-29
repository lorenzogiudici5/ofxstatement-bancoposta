#!/usr/bin/python3
"""Setup
"""
import os
from setuptools import find_packages
from setuptools.command.test import test as TestCommand
from distutils.core import setup

import unittest

version = "1.0.1"

setup(
    name="ofxstatement-bancoposta",
    version=version,
    author="Lorenzo Giudici",
    author_email="lorenzogiudici5@gmail.com",
    url="https://github.com/lorenzogiudici5/ofxstatement-bancoposta",
    description=("Bancoposta plugin for ofxstatement"),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="GPLv3",
    keywords=["ofx", "banking", "statement", "bancoposta"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "Natural Language :: English",
        "Topic :: Office/Business :: Financial :: Accounting",
        "Topic :: Utilities",
        "Environment :: Console",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    packages=find_packages("src"),
    package_dir={"": "src"},
    namespace_packages=["ofxstatement", "ofxstatement.plugins"],
    entry_points={
        "ofxstatement":
        [
            "bancoposta = ofxstatement.plugins.bancoposta:BancoPostaPlugin"
        ]
    },
    install_requires=["ofxstatement"],
    extras_require={"test": ["pytest"]},
    include_package_data=True,
    zip_safe=True,
)
