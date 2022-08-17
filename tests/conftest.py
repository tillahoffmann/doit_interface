import colorama
import doit_interface as di
import os
import pytest
import re
import tempfile
from unittest import mock


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


def get_mocked_stdout(write: mock.MagicMock) -> str:
    """
    Get the text written to a mocked :meth:`sys.stdout.write`.
    """
    write.assert_called()
    text = "".join(arg for (arg,), _ in write.call_args_list)
    return re.sub(colorama.AnsiToWin32.ANSI_CSI_RE, "", text)
