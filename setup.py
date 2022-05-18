from codecs import open
from setuptools import setup, find_packages
import sys

VERSION = "1.0"

try:
    with open('pxeutil/__main__.py', 'r', encoding='utf-8') as f:
        content = f.read()
except OSError:
    pass
else:
    import re

    m = re.search(r'__version__\s*=\s*[\'"](.+?)[\'"]', content)
    if not m:
        print('Could not find __version__ in pxeutil/__main__.py')
        sys.exit(1)
    if m.group(1) != VERSION:
        print('Expected __version__ = "{}"; found "{}"'.format(VERSION, m.group(1)))
        sys.exit(1)

CLASSIFIERS = [
    'Development Status :: 1 - Development',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'License :: OSI Approved :: MIT License',
]

DEPENDENCIES = [
    'jinja2',
    'netaddr',
    'pyaml'
]

with open('README.md', 'r', encoding='utf-8') as f:
    README = f.read()

setup(
    name='pxeutil',
    version=VERSION,
    description='Utility to manage PXE boot images',
    long_description=README,
    license='MIT',
    author='Nilson Lopes',
    author_email='noslin005@gmail.com',
    url='https://github.com/noslin/pxeutil',
    zip_safe=False,
    classifiers=CLASSIFIERS,
    scripts=[
        'pxu'
    ],
    packages=find_packages(exclude=["db", "docs", "templates", "tests"]),
    install_requires=DEPENDENCIES,
    python_requires='>=3.6.0',
)
