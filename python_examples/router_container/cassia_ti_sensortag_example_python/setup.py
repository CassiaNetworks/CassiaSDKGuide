# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='TI SensorTag CC2650STK Container App Example (Python) - Scan, Connect, Read, and Store',
    version='0.1.0',
    description='This Python application is an example Cassia router container app that shows how to scan, connect, and read data from the TI SensorTag CC2650STK and store it on the Cassia router container storage.',
    long_description=readme,
    author='Kevin Yang',
    author_email='kevin@cassianetworks.us',
    url='',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)