#!/usr/bin/python

from setuptools import setup, find_packages
import nose

setup(
    name="kernel-tools",
    version="0.0.1",
    description="Automatic kernel configuration and building in Gentoo and building in Gentoo",
    scripts=["user-config.py"],
    packages=find_packages(),
    testssuite=nose.collector
)
