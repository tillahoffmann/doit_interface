from setuptools import find_packages, setup


try:
    with open("VERSION") as fp:
        VERSION = fp.read().strip()
except FileNotFoundError:
    VERSION = "dev"


setup(
    name="doit_interface",
    packages=find_packages(),
    version=VERSION,
    install_requires=[
        "doit",
    ],
    extras_require={
        "tests": [
            "flake8",
            "pytest",
            "pytest-cov",
        ],
        "docs": [
            "sphinx",
        ]
    }
)
