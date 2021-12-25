#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='shapefile',
    version='0.0.1',
    author='Daniel King',
    author_email='daniel.zidan.king+shapefile@gmail.com',
    description='Read shapefiles and write geojson.',
    project_urls={
        'Repository': 'https://github.com/danking/shapefile',
    },
    packages=find_packages('.'),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.6',
    install_requires=[]
)
