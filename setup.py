#!/usr/bin/env python3
from setuptools import setup

setup(
    name="pytest_tracerobot",
    version="0.2.0",
    # the following makes a plugin available to pytest
    entry_points={"pytest11": ["name_of_plugin=pytest_tracerobot"]},
    # custom PyPI classifier for pytest plugins
    classifiers=["Framework :: Pytest"],
    install_requires=["tracerobot >= 0.1.0", "pytest >= 4.3.0"]
)
