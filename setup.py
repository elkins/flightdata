#!/usr/bin/env python3
"""Setup script for flightdata package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="flightdata",
    version="2.0.0",
    description="Python library to fetch flight data from ADS-B Exchange",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="George Elkins",
    url="https://github.com/elkins/flightdata",
    py_modules=["adsbexchange", "flight_logger"],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "mypy>=1.5.0",
            "ruff>=0.0.290",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="aviation flight tracking ads-b adsb-exchange aircraft",
)
