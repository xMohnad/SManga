from setuptools import setup, find_packages

setup(
    name="SManga",
    version="0.3",
    description="A CLI tool for scraping manga chapters using Scrapy",
    packages=find_packages(),
    install_requires=[
        "scrapy>=2.11.2",
        "pycryptodome>=3.20.0",
        "Click>=8.1.7",
        "windows-curses; platform_system=='Windows'",
        "click-completion",
    ], # "scrapy-fake-useragent>=1.4.0",
    entry_points={
        "console_scripts": [
            "SManga=SManga.core.cli:cli",
            "smanga=SManga.core.cli:cli",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
