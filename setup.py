""" Setuptools for Inferex-CLI """

from setuptools import find_packages, setup

setup(
    name="inferex",
    version="0.1.0",
    description="Inferex CLI - Init, deploy and manage your projects on Inferex infrastructure",
    url="https://inferex.com",
    author_email="alain@inferex.com",
    install_requires=["typer", "requests", "yaspin", "GitPython",
                      "PyYAML", "Cerberus", "requests_toolbelt", "progress"],
    packages=find_packages(exclude=['tests', 'inferex.decorator.tests']),
    package_data={"": ["inferex/template"]},
    include_package_data=True,
    entry_points={"console_scripts": ["inferex = inferex.__main__:main"]},
    keywords=["inferex"],
    zip_safe=False,
)
