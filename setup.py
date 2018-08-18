import os
# from setuptools import setup
from distutils.core import setup

import py2exe

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


############ NUMPY FIX FOR PY2EXE####################
import numpy
import sys

# add any numpy directory containing a dll file to sys.path
def numpy_dll_paths_fix():
    paths = set()
    np_path = numpy.__path__[0]
    for dirpath, _, filenames in os.walk(np_path):
        for item in filenames:
            if item.endswith('.dll'):
                paths.add(dirpath)

    sys.path.append(*list(paths))

numpy_dll_paths_fix()
######################################################

import matplotlib
setup(
    data_files=matplotlib.get_py2exe_datafiles(),
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
    options = {
        "py2exe":{
            'excludes': ['_gtkagg', '_tkagg'],
            "dll_excludes": ["MSVCP90.dll", "HID.DLL", "w9xpopen.exe", "libgdk-win32-2.0-0.dll", "libgobject-2.0-0.dll"],
            'packages': [
                "numpy",
                "requests",
                "lxml",
                "prettytable",
                "fuzzywuzzy",
                "pyperclip"
            ],
            "includes": ["matplotlib.backends.backend_tkagg"]
        }
    }
)