"""
Setup script for ctrader_async package.
"""

from setuptools import setup, find_packages

from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="ctrader-async",
    version="0.1.0",
    author="cTrader Async Contributors",
    author_email="",
    description="Modern async Python client for cTrader Open API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ctrader-async",
    packages=find_packages(where="src", exclude=["tests", "tests.*", "examples", "examples.*", "**/__pycache__*", "**/*.pyc"]),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    install_requires=[
        "protobuf>=4.25.0,<6.0",
        "typing_extensions>=4.12.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
    },
    keywords="ctrader trading forex api async asyncio",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/ctrader-async/issues",
        "Source": "https://github.com/yourusername/ctrader-async",
        "Documentation": "https://ctrader-async.readthedocs.io",
    },
)
