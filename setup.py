import re
from setuptools import find_packages, setup


try:
    with open("VERSION") as fp:
        VERSION = fp.read().strip()
except FileNotFoundError:
    VERSION = "dev"

with open("README.rst") as fp:
    long_description = fp.read()
substitutions = [
    (r":(attr|class|meth|ref):", r":code:"),
    (r".. doctest::.*", r".. code-block:: python"),
    (r".. automodule::", r".. code-block::\n\n"),
]
for pattern, repl in substitutions:
    long_description = re.sub(pattern, repl, long_description)

setup(
    name="doit_interface",
    description="A functional interface for creating doit tasks",
    packages=find_packages(),
    version=VERSION,
    install_requires=[
        "colorama",
        "doit",
    ],
    url="https://github.com/tillahoffmann/doit_interface",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    extras_require={
        "tests": [
            "flake8",
            "pytest",
            "pytest-cov",
            "twine",
        ],
        "docs": [
            "sphinx",
            "sphinx_rtd_theme",
            "docutils<0.18",
        ],
    },
    entry_points={
        "doit.REPORTER": [
            "doit_interface = doit_interface.reporters:DoitInterfaceReporter",
        ],
    },
)
