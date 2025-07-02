#!/usr/bin/env python3
"""Setup script for Dify KB Recall Testing Tool."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="dify-kb-recall-tester",
    version="1.0.0",
    author="KB Testing Team",
    author_email="team@example.com",
    description="A comprehensive tool for testing and analyzing recall performance of Dify knowledge base systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/dify-kb-recall-tester",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "web": [
            "flask>=2.0",
            "flask-cors>=3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "kb-tester=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.csv", "*.md"],
    },
)