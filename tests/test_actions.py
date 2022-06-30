import doit_utilities as du
import os
from unittest import mock
import sys


def test_subprocess_env(manager: du.Manager):
    manager(basename="inherit_env", actions=[du.SubprocessAction([])])
    manager(basename="update_env", actions=[du.SubprocessAction([], env={"OTHER_VAR": 17})])
    manager(basename="replace_env", actions=[
        du.SubprocessAction([], env={"OTHER_VAR": 19}, inherit_env=False)])

    try:
        os.environ["DOIT_UTILITIES_TEST_VAR"] = "VALUE"
        with mock.patch("subprocess.check_call") as check_call:
            manager.doit_main.run(["inherit_env"])
            check_call.assert_called_once()
            _, kwargs = check_call.call_args
            assert kwargs["env"]["DOIT_UTILITIES_TEST_VAR"] == "VALUE"
            assert "OTHER_VAR" not in kwargs["env"]
            check_call.reset_mock()

            manager.doit_main.run(["update_env"])
            check_call.assert_called_once()
            _, kwargs = check_call.call_args
            assert kwargs["env"]["DOIT_UTILITIES_TEST_VAR"] == "VALUE"
            assert kwargs["env"]["OTHER_VAR"] == "17"
            check_call.reset_mock()

            manager.doit_main.run(["replace_env"])
            check_call.assert_called_once()
            _, kwargs = check_call.call_args
            assert "DOIT_UTILITIES_TEST_VAR" not in kwargs["env"]
            assert kwargs["env"]["OTHER_VAR"] == "19"
            check_call.reset_mock()
    finally:
        os.environ.pop("DOIT_UTILITIES_TEST_VAR")


def test_subprocess_global_env(manager: du.Manager):
    manager(basename="task", actions=[du.SubprocessAction([])])

    with mock.patch("subprocess.check_call") as check_call:
        try:
            # Two ways to set global environment variables.
            du.SubprocessAction.set_global_env({"DOIT_UTILITIES_TEST_VAR": "SOMETHING"})
            du.SubprocessAction.get_global_env().update({
                "DOIT_UTILITIES_OTHER_TEST_VAR": "SOMETHING_ELSE"})

            manager.doit_main.run(["task"])
            check_call.assert_called_once()
            _, kwargs = check_call.call_args
            assert kwargs["env"]["DOIT_UTILITIES_TEST_VAR"] == "SOMETHING"
            assert kwargs["env"]["DOIT_UTILITIES_OTHER_TEST_VAR"] == "SOMETHING_ELSE"
            check_call.reset_mock()
        finally:
            du.SubprocessAction.set_global_env({})

        manager.doit_main.run(["task"])
        check_call.assert_called_once()
        _, kwargs = check_call.call_args
        assert "DOIT_UTILITIES_TEST_VAR" not in kwargs["env"]
        assert "DOIT_UTILITIES_OTHER_TEST_VAR" not in kwargs["env"]
        check_call.reset_mock()


def test_subprocess_substitutions(manager: du.Manager, tmpwd: str):
    # Create dependency files so we can run doit.
    for filename in ["dep1", "dep2"]:
        with open(filename, "w") as fp:
            fp.write(filename)

    tasks = [
        ("no_target", ["$@"], {}),
        ("no_multiple_deps", ["$^"], {}),
        ("interpreter", ["$!"], {}),
        ("target", ["$@"], {"targets": ["target1", "target2"]}),
        ("single_dep", ["$<"], {"file_dep": ["dep1", "dep2"]}),
        ("multiple_dep", ["$^"], {"file_dep": ["dep1", "dep2"]}),
    ]
    for basename, args, kwargs in tasks:
        manager(basename=basename, actions=[du.SubprocessAction(args)], **kwargs)

    for task in ["no_target", "no_multiple_deps"]:
        assert manager.doit_main.run([task])

    with mock.patch("subprocess.check_call") as check_call:
        assert not manager.doit_main.run(["interpreter"])
        check_call.assert_called_once()
        (args, *_), _ = check_call.call_args
        assert args == [sys.executable]
        check_call.reset_mock()

        assert not manager.doit_main.run(["target"])
        check_call.assert_called_once()
        (args, *_), _ = check_call.call_args
        assert args == ["target1"]
        check_call.reset_mock()

        assert manager.doit_main.run(["single_dep"])
        check_call.assert_not_called()
        check_call.reset_mock()

        assert not manager.doit_main.run(["multiple_dep"])
        check_call.assert_called_once()
        (args, *_), _ = check_call.call_args
        # doit uses sets for file dependencies so the order is non-deterministic.
        assert set(args) == {"dep1", "dep2"}
        check_call.reset_mock()
