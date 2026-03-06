"""
SeisLab Setup Script
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="seislab",
    version="1.0.0",
    author="SeisLab Development Team",
    description="Professional Seismic Analysis & Attribute Extraction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "matplotlib>=3.4.0",
        "PyQt5>=5.15.0",
        "netCDF4>=1.6.0",
        "xarray>=2023.1.0",
        "scikit-learn>=0.24.0",
    ],
    extras_require={
        "segy": ["segyio>=1.9.0"],
        "netcdf": ["netCDF4>=1.6.0", "xarray>=2023.1.0"],
        "advanced": ["pyqtgraph>=0.12.0"],
    },
    entry_points={
        "console_scripts": [
            "seislab=main:main",
        ],
    },
)
