import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "market_buddy",
    version = "0.1.0",
    author = "Nick Emery",
    author_email = "nickemery23@gmail.com",
    description = ("A command line program allowing fast interaction with warframe.market."),
    license = "MIT",
    keywords = "warframe warframe.market trading",
    url = "http://packages.python.org/market_buddy",
    packages=['market_buddy'],
    long_description=read('README.txt'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
    console=['market_buddy/market_buddy.py'],
    install_requires=[
        "matplotlib",
        "fuzzywuzzy",
        "pyperclip",
        "lxml",
        "prettytable",
        "python-Levenshtein"
    ]
)
