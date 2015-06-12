#!/usr/bin/env python

from distutils.core import setup


def readme():
    f = open('README.md')
    info = f.read()
    f.close()
    return info


setup(
    name='colordiffs',
    version='1.0',
    description='Syntax highlights for your git diffs',
    author='Ng Zhi An',
    author_email='ngzhian@gmail.com',
    url='https://github.com/ngzhian/colordiffs',
    scripts=['colordiffs.py'],
    long_description=readme(),
)
