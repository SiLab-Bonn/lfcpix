#!/usr/bin/env python

from setuptools import setup
from setuptools import find_packages
from platform import system

import numpy as np
import os

f = open('VERSION', 'r')
version = f.readline().strip()
f.close()

author = 'Toko Hirono'
author_email = 'hirono@physik.uni-bonn.de'

# requirements for core functionality
install_requires = ['basil-daq==2.4.3', 'bitarray>=0.8.1', 'matplotlib', 'numpy', 'pyyaml', 'scipy']

setup(
    name='lfcpix',
    version=version,
    description='DAQ for LFCPIX',
    url='https://github.com/SiLab-Bonn/lfcpix',
    license='',
    long_description='',
    author=author,
    maintainer=author,
    author_email=author_email,
    maintainer_email=author_email,
    install_requires=install_requires,
    packages=find_packages(),  
    include_package_data=True,  
    package_data={'': ['README.*', 'VERSION'], 'docs': ['*'], 'lfcpix': ['*.yaml', '*.bit']},
    platforms='any'
)
