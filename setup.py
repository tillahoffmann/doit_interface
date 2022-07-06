from setuptools import find_packages, setup


setup(
    name="doit_interface",
    packages=find_packages(),
    version="0.1.0",
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
