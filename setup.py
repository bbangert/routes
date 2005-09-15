from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

import sys
import os
from distutils.core import setup

setup(name="Routes",
      version='0.1',
      description='Routing Recognition and Generation Tools',
      long_description="""
A Routing package for Python that directly support 98% of the Rails unit tests
""",
      author='Ben Bangert',
      author_email='ben@groovie.org',
      url='http://routes.groovie.org/',
      packages=find_packages(exclude='tests'),
      )
      
