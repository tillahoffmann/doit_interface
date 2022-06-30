import doit_utilities as du


with du.Manager() as manager:
    manager(basename="tests", actions=["pytest -v --cov=doit_utilities --cov-fail-under=100 "
                                       "--cov-report=term-missing --cov-report=html"])
    manager(basename="lint", actions=["flake8"])

    with du.defaults(basename="docs"):
        manager(name="html", actions=["sphinx-build . docs/_build"])
        manager(name="tests", actions=["sphinx-build -b doctest . docs/_build"])

    with du.defaults(basename="requirements"):
        manager(name="test", targets=["test_requirements.txt"],
                file_dep=["test_requirements.in", "setup.py"],
                actions=["pip-compile -v -o %(targets)s test_requirements.in"])
        manager(name="dev", targets=["requirements.txt"],
                file_dep=["requirements.in", "setup.py", "test_requirements.txt"],
                actions=["pip-compile -v -o %(targets)s requirements.in"])
