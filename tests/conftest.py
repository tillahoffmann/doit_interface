import doit_interface as di
import os
import pytest
import tempfile


@pytest.fixture
def manager():
    with di.Manager() as manager:
        yield manager


@pytest.fixture(autouse=True)
def tmpwd():
    with tempfile.TemporaryDirectory() as tmp:
        cwd = os.getcwd()
        os.chdir(tmp)
        yield
        os.chdir(cwd)
