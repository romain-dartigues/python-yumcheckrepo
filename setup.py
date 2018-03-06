#!/usr/bin/env python
# vim:set ts=4 sw=4 ai et fileencoding=utf8:

# stdlib
import io
import os
import re

# dependencies
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup





PWD = os.path.dirname(os.path.abspath(__file__))
r_version = re.compile(r'__version__\s*=\s*(.*)')
_github_path = 'romain-dartigues/python-yumcheckrepo'

with io.open(os.path.join(PWD, 'yumcheckrepo.py'), 'rt', encoding='utf8') as fobj:
    version = re.search(
        r'''__version__\s*=\s*(?P<q>["'])(.*)(?P=q)''',
        fobj.read(),
        re.M,
    ).group(2)

with io.open('README.rst', 'rt', encoding='utf8') as fobj:
    README = fobj.read()
    long_description = README





setup(
    name='yumcheckrepo',
    version=version,
    description='a simplistic, Nagios-compatible, YUM repositories checker',
    long_description=long_description,
    author='Romain Dartigues',
    author_email='romain.dartigues@gmail.com',
    license='BSD 3-Clause License',
    keywords=('yum', 'nagios'),
    url='https://github.com/{}'.format(_github_path),
    download_url='https://api.github.com/repos/{}/tarball/{}'.format(
        _github_path,
        version,
    ),
    classifiers=(
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Monitoring',
    ),
    py_modules=(
        'yumcheckrepo',
    ),
    entry_points = {
        'console_scripts': ['yumcheckrepo=yumcheckrepo:main'],
    },
    zip_safe=True,
)
