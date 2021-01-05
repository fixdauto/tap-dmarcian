#!/usr/bin/env python
from setuptools import setup

setup(
    name="tap-dmarcian",
    version="0.1.0",
    description="Singer.io tap for extracting dmarcian report data from S3",
    author="FIXD Automotive, Inc.",
    url="http://github.com/fixdauto/tap-dmarcian",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_dmarcian"],
    install_requires=[
        "singer-python",
        "boto3"
    ],
    entry_points="""
    [console_scripts]
    tap-dmarcian=tap_dmarcian:main
    """,
    packages=["tap_dmarcian"],
    package_data = {
        "schemas": ["tap_dmarcian/schemas/*.json"]
    },
    include_package_data=True,
)
