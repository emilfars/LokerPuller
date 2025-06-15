"""
Setup script for LokerPuller.
"""

from setuptools import setup, find_packages
import os

# Read README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="lokerpuller",
    version="2.0.0",
    author="LokerPuller Team",
    author_email="team@lokerpuller.com",
    description="Southeast Asian Job Scraper and Management System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/lokerpuller",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pre-commit>=3.4.0",
        ],
        "prod": [
            "gunicorn>=21.2.0",
            "supervisor>=4.2.5",
        ]
    },
    entry_points={
        "console_scripts": [
            "lokerpuller=lokerpuller.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "lokerpuller": [
            "web/static/*",
            "web/templates/*",
        ],
    },
    keywords="jobs scraper southeast asia indonesia malaysia thailand vietnam singapore",
    project_urls={
        "Bug Reports": "https://github.com/your-username/lokerpuller/issues",
        "Source": "https://github.com/your-username/lokerpuller",
        "Documentation": "https://github.com/your-username/lokerpuller/docs",
    },
) 