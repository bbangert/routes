try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

version = '1.12.3'

setup(name="Routes",
      version=version,
      description='Routing Recognition and Generation Tools',
      long_description="""
A Routing package for Python that matches URL's to dicts and vice versa

`Dev version available <http://bitbucket.org/bbangert/routes/>`_
""",
      classifiers=["Development Status :: 5 - Production/Stable",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: BSD License",
                   "Programming Language :: Python",
                   "Topic :: Internet :: WWW/HTTP",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   ],
      author='Ben Bangert',
      author_email='ben@groovie.org',
      url='http://routes.groovie.org/',
      zip_safe=False,
      test_suite='nose.collector',
      tests_require=['nose', 'webtest', 'paste'],
      packages=find_packages(exclude=['tests', 'ez_setup']),
      )
