"""
Setup script for shared libraries
"""

from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="energy-tracking-libs",
    version="1.0.0",
    description="Shared libraries for Energy Tracking IoT Platform",
    author="Energy Tracking Team",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
