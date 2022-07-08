import doit_interface as di
import os
import pytest
import sys
from unittest import mock


def test_subprocess_env(manager: di.Manager, tmpwd: str):
    manager(basename="inherit_env", actions=[di.SubprocessAction([])])
    manager(basename="update_env", actions=[di.SubprocessAction([], env={"OTHER_VAR": 17})])
    manager(basename="replace_env", actions=[
        di.SubprocessAction([], env={"OTHER_VAR": 19}, inherit_env=False)])

    try:
        os.environ["doit_interface_TEST_VAR"] = "VALUE"
        with mock.patch("subprocess.check_call") as check_call:
            manager.doit_main.run(["inherit_env"])
            check_call.assert_called_once()
            _, kwargs = check_call.call_args
            assert kwargs["env"]["doit_interface_TEST_VAR"] == "VALUE"
            assert "OTHER_VAR" not in kwargs["env"]
            check_call.reset_mock()

            manager.doit_main.run(["update_env"])
            check_call.assert_called_once()
            _, kwargs = check_call.call_args
            assert kwargs["env"]["doit_interface_TEST_VAR"] == "VALUE"
            assert kwargs["env"]["OTHER_VAR"] == "17"
            check_call.reset_mock()

            manager.doit_main.run(["replace_env"])
            check_call.assert_called_once()
            _, kwargs = check_call.call_args
            assert "doit_interface_TEST_VAR" not in kwargs["env"]
            assert kwargs["env"]["OTHER_VAR"] == "19"
            check_call.reset_mock()
    finally:
        os.environ.pop("doit_interface_TEST_VAR")


def test_subprocess_global_env(manager: di.Manager, tmpwd: str):
    manager(basename="task", actions=[di.SubprocessAction([])])

    with mock.patch("subprocess.check_call") as check_call:
        try:
            # Two ways to set global environment variables.
            di.SubprocessAction.set_global_env({"doit_interface_TEST_VAR": "SOMETHING"})
            di.SubprocessAction.get_global_env().update({
                "doit_interface_OTHER_TEST_VAR": "SOMETHING_ELSE"})

            manager.doit_main.run(["task"])
            check_call.assert_called_once()
            _, kwargs = check_call.call_args
            assert kwargs["env"]["doit_interface_TEST_VAR"] == "SOMETHING"
            assert kwargs["env"]["doit_interface_OTHER_TEST_VAR"] == "SOMETHING_ELSE"
            check_call.reset_mock()
        finally:
            di.SubprocessAction.set_global_env({})

        manager.doit_main.run(["task"])
        check_call.assert_called_once()
        _, kwargs = check_call.call_args
        assert "doit_interface_TEST_VAR" not in kwargs["env"]
        assert "doit_interface_OTHER_TEST_VAR" not in kwargs["env"]
        check_call.reset_mock()


@pytest.mark.parametrize("shell", [True, False])
def test_subprocess_substitutions(manager: di.Manager, tmpwd: str, shell: bool):
    def _maybe_join(x):
        if shell:
            x = " ".join(x)
        return x

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
        ("name_sub", ["echo", "hello {name}"], {}),
    ]
    for basename, args, kwargs in tasks:
        manager(basename=basename, actions=[di.SubprocessAction(_maybe_join(args))], **kwargs)

    for task in ["no_target", "no_multiple_deps"]:
        assert manager.doit_main.run([task])

    with mock.patch("subprocess.check_call") as check_call:
        assert not manager.doit_main.run(["interpreter"])
        check_call.assert_called_once()
        (args, *_), _ = check_call.call_args
        assert args == _maybe_join([sys.executable])
        check_call.reset_mock()

        assert not manager.doit_main.run(["target"])
        check_call.assert_called_once()
        (args, *_), _ = check_call.call_args
        assert args == _maybe_join(["target1"])
        check_call.reset_mock()

        assert manager.doit_main.run(["single_dep"])
        check_call.assert_not_called()
        check_call.reset_mock()

        assert not manager.doit_main.run(["multiple_dep"])
        check_call.assert_called_once()
        (args, *_), _ = check_call.call_args
        # doit uses sets for file dependencies so the order is non-deterministic.
        assert set(args.split() if shell else args) == {"dep1", "dep2"}
        check_call.reset_mock()

        assert not manager.doit_main.run(["name_sub"])
        check_call.assert_called_once()
        (args, *_), _ = check_call.call_args
        assert args == _maybe_join(["echo", "hello name_sub"])
        check_call.reset_mock()


def test_subprocess_invalid_args(manager: di.Manager, tmpwd: str):
    manager(basename="task", actions=[di.SubprocessAction(74)])
    assert manager.doit_main.run([])


def test_subprocess_shell(manager: di.Manager, tmpwd: str):
    manager(basename="task", actions=[di.SubprocessAction("echo hello > world.txt")])
    manager.doit_main.run([])
    with open("world.txt") as fp:
        assert fp.read().strip() == "hello"


def test_subprocess_use_as_default(manager: di.Manager):
    with di.SubprocessAction.use_as_default():
        task = manager(basename="task", actions=["echo hello"])
    assert isinstance(task["actions"][0], di.SubprocessAction)
