# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name=('cassiadevtools'),
    version='0.1.0',
    description=('This Python package contains modules that might be '
                 'handy when developing with the Cassia SDK RESTful API.'),
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
    keywords=('cassia networks, cassia, cassia sdk restful api, cassia sdk,'
              'cassia restful, cassia restful api, cassia sdk api, cassia api'
              'cassia dev tools, cassia tools, cassiadevtools'),
    package_dir={'': 'src'},
    license=license,
    packages=find_packages(where='src'),
    python_requires='>=3.8, <4',
    install_requires=['pytest==6.0.2', 'sphinx==3.2.1', 'click==7.1.2', 'aiohttp-sse-client==0.1.7'],
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },
    entry_points={
        'console_scripts': [
            ('container_ti_sensortag_example='
             'cassiadevtools.scripts.container_ti_sensortag_example:main'),
        ],
    },
    project_urls={
        'Bug Reports': 'https://www.cassianetworks.com/support',
        'Products': 'https://www.cassianetworks.com/products',
        'Contact Us': 'https://www.cassianetworks.com/contact-us',
        # TODO: Edit Source once project is fully uploaded on master branch!
        'Source': ('https://github.com/CassiaNetworks/CassiaSDKGuide/tree'
                   '/master/python_examples'),
    },
)
