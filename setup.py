#
#  setup
#
#  Created by Ben Bangert on 2005-08-09.
#  Copyright (c) 2005 Parachute. All rights reserved.
#

import sys
import os
from distutils.core import setup

setup(name="routes",
      version='0.1',
      description='Routing Recognition and Generation Tools',
      author='Ben Bangert',
      author_email='ben@groovie.org',
      url='http://routes.groovie.org/',
      package_dir = {'': 'lib'},
      packages = ['routes']
      )