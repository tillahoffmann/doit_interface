import doit_interface as di


manager = di.Manager.get_instance()

with di.group_tasks("build"):
    manager(basename="tests", actions=["pytest -v --cov=doit_interface --cov-fail-under=100 "
                                       "--cov-report=term-missing --cov-report=html"])
    manager(basename="lint", actions=["flake8"])

    with di.defaults(basename="docs"):
        manager(name="html", actions=["sphinx-build -n . docs/_build"])
        manager(name="tests", actions=["sphinx-build -b doctest . docs/_build"])

    with di.defaults(basename="package"):
        task = manager(name="wheel", actions=["$! -m build ."])
        manager(name="check", actions=["twine check dist/*"], task_dep=[task])
        manager(name="pypi-readme", file_dep=["README.rst", "setup.py"],
                targets=["docs/_build/pypi.html"], actions=["$! pypi-readme.py $@"])

with di.defaults(basename="requirements"):
    manager(name="test", targets=["test_requirements.txt"],
            file_dep=["test_requirements.in", "setup.py"],
            actions=["pip-compile -v -o $@ test_requirements.in"])
    manager(name="dev", targets=["requirements.txt"],
            file_dep=["requirements.in", "setup.py", "test_requirements.txt"],
            actions=["pip-compile -v -o $@ requirements.in"])
    manager(name="sync", file_dep=["requirements.txt"], actions=["pip-sync requirements.txt"])
