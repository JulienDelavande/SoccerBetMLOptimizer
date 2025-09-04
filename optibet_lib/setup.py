from setuptools import setup, find_packages
import os

# Read requirements from requirements.txt if it exists
here = os.path.abspath(os.path.dirname(__file__))
requirements_path = os.path.join(here, 'requirements.txt')

install_requires = []
if os.path.exists(requirements_path):
    with open(requirements_path, 'r', encoding='utf-8') as f:
        install_requires = [
            line.strip() for line in f 
            if line.strip() and not line.startswith('#')
        ]

# Read long description from README if it exists
long_description = ""
readme_path = os.path.join(here, 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()

setup(
    name='optibet_lib',
    version='0.4.0',
    description='Shared library for OptiBet soccer betting ML optimizer',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Julien Delavande',
    author_email='julien.delavande@example.com',
    packages=find_packages(where='optibet_lib'),
    package_dir={'': 'optibet_lib'},
    python_requires='>=3.10',
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Office/Business :: Financial :: Investment',
    ],
    keywords='betting, machine learning, soccer, optimization, sports',
    project_urls={
        'Bug Reports': 'https://github.com/JulienDelavande/SoccerBetMLOptimizer/issues',
        'Source': 'https://github.com/JulienDelavande/SoccerBetMLOptimizer',
    },
)