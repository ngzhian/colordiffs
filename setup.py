#!/usr/bin/env python

from distutils.core import setup


def readme():
    f = open('README')
    info = f.read()
    f.close()
    return info


setup(
    name='colordiffs',
    version='0.1.3',
    description='Syntax highlights for your git diffs',
    author='Ng Zhi An',
    author_email='ngzhian@gmail.com',
    url='https://github.com/ngzhian/colordiffs',
    py_modules=['colordiffs'],
    long_description=readme(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ],
    install_requires=[
        "Pygments>=2.0.2",
    ],
    scripts=['scripts/colordiffs'],
)
