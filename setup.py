from setuptools import setup, find_packages

def parse_requirements(filename):
    with open(filename, "r", encoding="utf8") as f:
        requirements = f.read().strip().split("\n")
        requirements = [
            r.strip() for r in requirements if r.strip() and not r.startswith("#")
        ]
        return requirements

setup(
    name="SManga",
    version="0.3.2",
    description="A CLI tool for scraping manga chapters using Scrapy",
    packages=find_packages(),
    install_requires=parse_requirements("requirements.txt"),
    entry_points={
        "console_scripts": [
            "smanga=SManga.core.cli:app",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
