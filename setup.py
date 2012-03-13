__version__ = '1.13'

import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGELOG.rst')).read()


setup(name="Routes",
      version=__version__,
      description='Routing Recognition and Generation Tools',
      long_description=README + '\n\n' +CHANGES,
      classifiers=["Development Status :: 5 - Production/Stable",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: BSD License",
                   "Programming Language :: Python",
                   "Topic :: Internet :: WWW/HTTP",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   ],
      keywords='routes webob dispatch',
      author="Ben Bangert",
      author_email="ben@groovie.org",
      url='http://routes.groovie.org/',
      license="MIT",
      packages=find_packages(),
      test_suite="nose.collector",
      include_package_data=True,
      zip_safe=False,
      tests_require=['nose', 'webtest', 'webob', 'coverage'],
      install_requires=[
          "repoze.lru>=0.3"
      ],
      packages=find_packages(exclude=['tests', 'ez_setup']),
)
