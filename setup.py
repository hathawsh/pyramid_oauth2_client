
from setuptools import setup, find_packages
import os
import sys

requires = [
    'pyramid',
    'requests',
    'setuptools',
]

if sys.version_info[:2] < (2, 7):
    requires.append('unittest2')

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

setup(
    name='pyramid_oauth2_client',
    version='0.1',
    description='Library for authenticating Pyramid apps using OAuth2',
    long_description=README + '\n\n' +  CHANGES,
    classifiers=[
        "Programming Language :: Python",
    ],
    author='',
    author_email='',
    url='',
    keywords='',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    test_suite='pyramid_oauth2_client',
    install_requires=requires,
)
