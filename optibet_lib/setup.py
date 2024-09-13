from setuptools import setup, find_packages

# python setup.py bdist_wheel

setup(
    name='optibet_lib',
    version='0.2',
    packages=find_packages(where='optibet_lib'),
    package_dir={'': 'optibet_lib'},
)