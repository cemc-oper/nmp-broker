# coding=utf-8
from setuptools import setup, find_packages

setup(
    name='nmp-broker',

    version='1.0.0',

    description='A broker for NWPC monitor platform.',
    long_description=__doc__,

    packages=find_packages(exclude=['conf', 'docs', 'tests', 'templates', 'static']),

    include_package_data=True,

    zip_safe=False,

    install_requires=[
        'click',
        'Flask',
        'Flask-SQLAlchemy',
        'mysql-connector-python',
        'pymongo',
        'PyYAML',
        'redis',
        'requests',
        'SQLAlchemy',
        'backports-datetime-fromisoformat;python_version<"3.7"'
    ]
)