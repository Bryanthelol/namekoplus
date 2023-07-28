from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='namekoplus',
    version='0.4.0',
    description='A lightweight Python distributed microservice solution',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='',
    project_urls={
        'Documentation': 'https://doc.bearcatlog.com/',
        'Source Code': 'https://github.com/Bryanthelol/namekoplus',
        'Bug Tracker': 'https://github.com/Bryanthelol/namekoplus/issues',
    },
    author='Bryant He',
    author_email='bryantsisu@qq.com',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    platforms='any',
    python_requires='>=3.8, <4',

    keywords='lightweight python distributed microservice solution',

    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    include_package_data=True,
    data_files=['README.md'],

    entry_points={
        'console_scripts': [
            'namekoplus = namekoplus.command:cli',
        ],
    },

    install_requires=[
        'nameko==3.0.0rc11',
        'click==8.1.5',
        'python-on-whales==0.63.0',
        'pytest==7.4.0',
        'mako==1.2.4',
        'shortuuid==1.0.11'
    ],
    extras_require={
        'ha': ['tenacity==8.2.2',
               'cachetools==5.3.0',
               'circuitbreaker==2.0.0',
               'statsd==4.0.1',
               'logstash_formatter==0.5.17',
               'nameko-sentry==1.0.0',
               'nameko-tracer==1.4.0'],
        'apiflask': ['apiflask>=1.3.1',
                     'gevent>=22.10.2',
                     'gunicorn==20.1.0'],
        'rocketry': ['rocketry==2.4.0'],
        'gutter': ['gutter==0.5.0'],
        'mysql': ['pymysql==1.0.3',
                  'sqlalchemy==2.0.15',
                  'sqlacodegen==2.3.0',
                  'alembic==1.11.1'],
        'security': ['cryptography'],
        'dev': ['environs==9.5.0']
    },
)
