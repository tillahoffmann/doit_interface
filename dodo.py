import doit_interface as di


manager = di.Manager.get_instance()

with di.group_tasks("build"):
    manager(basename="tests", actions=["pytest -v --cov=doit_interface --cov-fail-under=100 "
                                       "--cov-report=term-missing --cov-report=html"])
    manager(basename="lint", actions=["flake8"])

    with di.defaults(basename="docs"):
        manager(name="html", actions=["sphinx-build . docs/_build"])
        manager(name="tests", actions=["sphinx-build -b doctest . docs/_build"])

    manager(basename="version", actions=["python version.py"], file_dep=["version.py"],
            targets=["VERSION"])

    with di.defaults(basename="package"):
        try:
            with open("VERSION") as fp:
                version = fp.read().strip()
        except FileNotFoundError:
            version = "dev"
        archive = f"dist/doit_interface-{version}.tar.gz"
        manager(name="sdist", actions=[di.SubprocessAction(["$!", "setup.py", "sdist"])],
                targets=[archive])
        manager(name="check", file_dep=[archive],
                actions=[di.SubprocessAction(["twine", "check", archive])])
        manager(name="pypi-readme", file_dep=["README.rst", "setup.py"],
                targets=["docs/_build/pypi.html"],
                actions=[di.SubprocessAction(["$!", "pypi-readme.py", "$@"])])

with di.defaults(basename="requirements"):
    manager(name="test", targets=["test_requirements.txt"],
            file_dep=["test_requirements.in", "setup.py"],
            actions=["pip-compile -v -o %(targets)s test_requirements.in"])
    manager(name="dev", targets=["requirements.txt"],
            file_dep=["requirements.in", "setup.py", "test_requirements.txt"],
            actions=["pip-compile -v -o %(targets)s requirements.in"])
