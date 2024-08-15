from setuptools import setup, find_packages

setup(
    name="SManga",
    version="0.1",
    description="A Scrapy-based library for scraping manga chapters",
    packages=find_packages(),
    install_requires=[
        "scrapy>=2.11.2",
        "pycryptodome>=3.20.0",
        "Click>=8.1.7",
        "validators",
    ],
    entry_points={
        "console_scripts": [
            "SManga=SManga.cli:cli",
            "smanga=SManga.cli:cli",
        ],
    },
)
