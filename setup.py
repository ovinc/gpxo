from setuptools import setup, find_packages
import gpxo

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name='gpxo',
    version=gpxo.__version__,
    author='Olivier Vincent',
    author_email='olivier.vincent@univ-lyon1.fr',
    url='https://cameleon.univ-lyon1.fr/ovincent/gpxo',
    description='Additional Image Analysis Tools',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    setup_requires=['numpy', 'vincenty', 'gpxpy'],
    python_requires='>=3.6'
)
