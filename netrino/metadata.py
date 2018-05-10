# -*- coding: utf-8 -*-
"""Project metadata

Information describing the project.
"""

# The package name, which is also the "UNIX name" for the project.
package = 'netrino'
project = "Tachyonic Project " + package.title()
project_no_spaces = project.replace(' ', '')
# Please follow https://www.python.org/dev/peps/pep-0440/
version = '0.0.0'
description = project
author = 'Myria Solutions (PTY) Ltd'
email = 'project@tachyonic.org'
license = 'BSD3-Clause'
copyright = '2018 ' + author
url = 'http://www.tachyonic.org'
identity = project + ' v' + version

# Classifiers
# <http://pypi.python.org/pypi?%3Aaction=list_classifiers>
classifiers = [
    'Development Status :: 1 - Planning',
    'Environment :: Other Environment',
    'Intended Audience :: Developers',
    'Intended Audience :: Information Technology',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: BSD License',
    'Natural Language :: English',
    'Operating System :: POSIX :: Linux',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Topic :: Software Development',
    'Topic :: Software Development :: Libraries',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
    'Topic :: Internet :: WWW/HTTP',
    'Topic :: Internet :: WWW/HTTP :: WSGI',
    'Topic :: Internet :: WWW/HTTP :: WSGI :: Application'
    ]
