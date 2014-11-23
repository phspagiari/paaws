#!/usr/bin/env python
# -*- coding: utf-8 -*-
import setuptools
from setuptools import setup, find_packages


if setuptools.__version__ < '0.7':
    raise RuntimeError("setuptools must be newer than 0.7")


setup(
    name="paaws",
    version="0.1.0",
    author="Pedro H. Spagiari",
    author_email="phspagiari@gmail.com",
    description="",
    url="https://github.com/phspagiari/paaws",
    packages=find_packages(exclude=('tests',)),
    long_description=open('README.md').read(),
    zip_safe=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: Proprietary",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    install_requires=[
        "boto>=2.32.0",
        "docopt>=0.6.1",
        "prettytable==0.7.2",
        "Fabric==1.8.2",
    ],
    scripts=["bin/paaws"],
)
