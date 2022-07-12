import colorama
import doit_interface as di
import pytest
import re
from unittest import mock


def _get_text(write: mock.MagicMock):
    write.assert_called()
    text = "".join(arg for (arg,), _ in write.call_args_list)
    return re.sub(colorama.AnsiToWin32.ANSI_CSI_RE, "", text)


@pytest.mark.parametrize("with_meta", [True, False])
def test_reporter_traceback(manager: di.Manager, with_meta: bool):
    task = manager(basename="false", actions=["false"])
    if not with_meta:
        task.pop("meta")
    doit_main = manager.doit_main
    doit_main.task_loader.namespace["DOIT_CONFIG"] = {
        "reporter": di.DoitInterfaceReporter,
    }
    assert doit_main.run(["false"])


def test_reporter_labels(manager: di.Manager):
    manager(basename="success", actions=["true"])
    manager(basename="failed", actions=["false"])
    manager(basename="uptodate", actions=["touch file.txt"], targets=["file.txt"], uptodate=[True])

    doit_main = manager.doit_main
    doit_main.task_loader.namespace["DOIT_CONFIG"] = {
        "reporter": di.DoitInterfaceReporter,
    }

    with mock.patch("sys.stdout.write") as write:
        doit_main.run(["success"])
        stdout = _get_text(write)
    assert "EXECUTE: success" in stdout
    assert "SUCCESS: success" in stdout

    with mock.patch("sys.stdout.write") as write:
        doit_main.run(["failed"])
        stdout = _get_text(write)
    assert "EXECUTE: failed" in stdout
    assert "FAILED: failed" in stdout

    with mock.patch("sys.stdout.write") as write:
        doit_main.run(["uptodate"])
        stdout = _get_text(write)
    assert "EXECUTE: uptodate" in stdout
    assert "SUCCESS: uptodate" in stdout
    with mock.patch("sys.stdout.write") as write:
        doit_main.run(["uptodate"])
        stdout = _get_text(write)
    assert "UP TO DATE: uptodate" in stdout
