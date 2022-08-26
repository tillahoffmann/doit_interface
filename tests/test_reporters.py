import doit_interface as di
import pytest
import re
from unittest import mock
from .conftest import get_mocked_stdout


@pytest.mark.parametrize("with_meta", [True, False])
def test_reporter_traceback(manager: di.Manager, with_meta: bool):
    task = manager(basename="false", actions=["false"])
    if not with_meta:
        task.pop("meta")
    doit_main = manager.doit_main(DOIT_CONFIG={"reporter": di.DoitInterfaceReporter})
    with mock.patch("sys.stdout.write") as write:
        assert doit_main.run(["false"])
    if with_meta:
        assert re.search(r"false \(declared at .*?test_reporters.py:10\)", get_mocked_stdout(write))
    else:
        assert re.search(r"false \(declared at <unknown>\)", get_mocked_stdout(write))


def test_reporter_labels(manager: di.Manager):
    manager(basename="success", actions=["true"])
    manager(basename="failed", actions=["false"])
    manager(basename="uptodate", actions=["touch file.txt"], targets=["file.txt"], uptodate=[True])

    doit_main = manager.doit_main(DOIT_CONFIG={"reporter": di.DoitInterfaceReporter})

    with mock.patch("sys.stdout.write") as write:
        assert not doit_main.run(["success"])
        stdout = get_mocked_stdout(write)
    assert "EXECUTE: success" in stdout
    assert "SUCCESS: success" in stdout

    with mock.patch("sys.stdout.write") as write:
        assert doit_main.run(["failed"])
        stdout = get_mocked_stdout(write)
    assert "EXECUTE: failed" in stdout
    assert "FAILED: failed" in stdout

    with mock.patch("sys.stdout.write") as write:
        assert not doit_main.run(["uptodate"])
        stdout = get_mocked_stdout(write)
    assert "EXECUTE: uptodate" in stdout
    assert "SUCCESS: uptodate" in stdout
    with mock.patch("sys.stdout.write") as write:
        assert not doit_main.run(["uptodate"])
        stdout = get_mocked_stdout(write)
    assert "UP TO DATE: uptodate" in stdout
