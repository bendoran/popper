# -*- coding: utf-8 -*-


"""setup.py: setuptools control."""


import re
from setuptools import setup


version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('popper/popper.py').read(),
    re.M
    ).group(1)


with open("README.txt", "rb") as f:
    long_descr = f.read().decode("utf-8")
    
data_files = []

data_files.append(('/etc/init.d',['conf/debian/upstart/popper']))
data_files.append(('/etc/popper',['conf/popper.conf']))

setup(
    name = "Popper",
    packages = ["popper"],
    entry_points = {
        "console_scripts": ['popper = popper.popper:main']
        },
    version = version,
    description = "A lightweight automated scripting engine for GH, allowing Post Receive Hooks to be deployed to a single environment ",
    long_description = long_descr,
    author = "Ben Doran",
    author_email = "greppinfunk@gmail.com",
    url = "http://bdoran.co.uk",
    package_data = { 'conf' : ["conf/*"] },
    data_files=data_files
)