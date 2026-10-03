# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pyovobj",
    version="1.3.0",
    author="good9527",
    author_email="good9527@users.noreply.github.com",
    description="Native Ovital (.ovobj) Vector Decoding and Multi-Format GIS/CAD Conversion Toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/good9527/ovobj-converter",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    python_requires=">=3.9",
    install_requires=[
        "geopandas>=0.14.0",
        "shapely>=2.0.0",
        "pyproj>=3.6.0",
        "pandas>=2.0.0",
        "ezdxf>=1.4.0",
        "openpyxl>=3.1.0",
    ],
    entry_points={
        "console_scripts": [
            "ovobj-converter=pyovobj.cli:main",
        ],
    },
)
