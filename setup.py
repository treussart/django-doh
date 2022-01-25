import os
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-doh',
    version='0.1.1',
    packages=find_packages(),
    include_package_data=True,
    license='BSD License',
    description='A simple Django app to serve DOH.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/treussart/django-doh',
    author='Matthieu Treussart',
    author_email='matthieu@treussart.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: Name Service (DNS)',
    ],
    install_requires=[
        'django',
        'dnspython>=2.2',
    ],
    python_requires='>=3.6',
)
