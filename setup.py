""" Setuptools for Inferex-CLI """

from setuptools import find_packages, setup
import sys

sys.dont_write_bytecode = True

# Read requirements
with open('requirements.txt') as f:
    required = f.read().splitlines()

# Setup the package
setup(
    name="inferex",
    version="0.0.2",
    description="Inferex CLI - Init, deploy and manage your projects on Inferex infrastructure",
    url="https://inferex.com",
    author_email="alain@inferex.com",
    install_requires=required,
    packages=find_packages(exclude=["tests", "inferex.decorator.tests"]),
    package_data={"": ["inferex/template"]},
    include_package_data=True,
    entry_points={"console_scripts": ["inferex = inferex.__main__:main"]},
    keywords=["inferex"],
    zip_safe=False,
)
