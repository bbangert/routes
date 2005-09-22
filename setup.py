from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

setup(name="Routes",
      version='0.2',
      description='Routing Recognition and Generation Tools',
      long_description="""
A Routing package for Python that matches URL's to dicts and vice versa
""",
      classifiers=["Development Status :: 4 - Beta",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: BSD License",
                   "Programming Language :: Python",
                   "Topic :: Internet :: WWW/HTTP",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   ],
      author='Ben Bangert',
      author_email='ben@groovie.org',
      url='http://routes.groovie.org/',
      packages=find_packages(exclude=['tests', 'ez_setup']),
      )