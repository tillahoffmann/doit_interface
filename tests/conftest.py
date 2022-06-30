import doit_utilities as du
import os
import pytest
import tempfile


@pytest.fixture
def manager():
    with du.Manager() as manager:
        yield manager


@pytest.fixture
def tmpwd():
    with tempfile.TemporaryDirectory() as tmp:
        cwd = os.getcwd()
        os.chdir(tmp)
        yield
        os.chdir(cwd)
