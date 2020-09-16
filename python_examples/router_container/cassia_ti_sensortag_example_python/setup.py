# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name=('TI SensorTag CC2650STK Container App Example (Python) '
          '- Scan, Connect, Read, and Store'),
    version='0.1.0',
    description=('This Python application is an example Cassia router '
                 'container app that shows how to scan, connect, and read '
                 'data from the TI SensorTag CC2650STK and store it on the '
                 'Cassia router container storage.'),
    long_description=readme,
    author='Kevin Yang',
    author_email='kevin@cassianetworks.us',
    classifiers=[
        # How mature is this project?
        #   1 - Planning
        #   2 - Pre-Alpha
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 2 - Pre-Alpha',

        'Intended Audience :: Developers',
        'Topic :: Software Development',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3.8'
    ],
    keywords='sample, setuptools, development',
    package_dir={'': 'src'},
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    python_requires='>=3.8, <4',
    install_requires=['pytest', 'sphinx'],
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },
    entry_points={
        'console_scripts': [
            'cassiatidemo=cassiatidemo:main',
        ],
    },
    project_urls={
        'Bug Reports': 'https://www.cassianetworks.com/support',
        'Products': 'https://www.cassianetworks.com/products',
        'Contact Us': 'https://www.cassianetworks.com/contact-us',
        # TODO: Edit Source once project is fully uploaded on master branch!
        'Source': ('https://github.com/CassiaNetworks/CassiaSDKGuide/tree'
                   '/master/python_examples/'),
    },
)
