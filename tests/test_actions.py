import doit_interface as di
import os
import pytest
import sys
from unittest import mock
from .conftest import get_mocked_stdout


def test_subprocess_env(manager: di.Manager):
    manager(basename="inherit_env", actions=[di.SubprocessAction([])])
    manager(basename="update_env", actions=[di.SubprocessAction([], env={"OTHER_VAR": 17})])
    manager(basename="replace_env", actions=[
        di.SubprocessAction([], env={"OTHER_VAR": 19}, inherit_env=False)])

    try:
        os.environ["doit_interface_TEST_VAR"] = "VALUE"
        with mock.patch("subprocess.check_call") as check_call:
            assert not manager.run(["inherit_env"])
            check_call.assert_called_once()
            _, kwargs = check_call.call_args
            assert kwargs["env"]["doit_interface_TEST_VAR"] == "VALUE"
            assert "OTHER_VAR" not in kwargs["env"]
            check_call.reset_mock()

            assert not manager.run(["update_env"])
            check_call.assert_called_once()
            _, kwargs = check_call.call_args
            assert kwargs["env"]["doit_interface_TEST_VAR"] == "VALUE"
            assert kwargs["env"]["OTHER_VAR"] == "17"
            check_call.reset_mock()

            assert not manager.run(["replace_env"])
            check_call.assert_called_once()
            _, kwargs = check_call.call_args
            assert "doit_interface_TEST_VAR" not in kwargs["env"]
            assert kwargs["env"]["OTHER_VAR"] == "19"
            check_call.reset_mock()
    finally:
        os.environ.pop("doit_interface_TEST_VAR")


def test_subprocess_global_env(manager: di.Manager):
    manager(basename="task", actions=[di.SubprocessAction([])])

    with mock.patch("subprocess.check_call") as check_call:
        try:
            # Two ways to set global environment variables.
            di.SubprocessAction.set_global_env({"doit_interface_TEST_VAR": "SOMETHING"})
            di.SubprocessAction.get_global_env().update({
                "doit_interface_OTHER_TEST_VAR": "SOMETHING_ELSE"})

            assert not manager.run(["task"])
            check_call.assert_called_once()
            _, kwargs = check_call.call_args
            assert kwargs["env"]["doit_interface_TEST_VAR"] == "SOMETHING"
            assert kwargs["env"]["doit_interface_OTHER_TEST_VAR"] == "SOMETHING_ELSE"
            check_call.reset_mock()
        finally:
            di.SubprocessAction.set_global_env({})

        assert not manager.run(["task"])
        check_call.assert_called_once()
        _, kwargs = check_call.call_args
        assert "doit_interface_TEST_VAR" not in kwargs["env"]
        assert "doit_interface_OTHER_TEST_VAR" not in kwargs["env"]
        check_call.reset_mock()


@pytest.mark.parametrize("shell", [True, False])
def test_subprocess_substitutions(manager: di.Manager, shell: bool):
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
        assert manager.run([task]) == 3

    with mock.patch("subprocess.check_call") as check_call, \
            mock.patch("os.path.isfile", return_value=True) as isfile:
        assert not manager.run(["interpreter"])
        check_call.assert_called_once()
        (args, *_), _ = check_call.call_args
        assert args == _maybe_join([sys.executable])
        check_call.reset_mock()

        assert not manager.run(["target"])
        check_call.assert_called_once()
        (args, *_), _ = check_call.call_args
        assert args == _maybe_join(["target1"])
        check_call.reset_mock()
        assert {call_args[0] for call_args, _ in isfile.call_args_list} == {"target1", "target2"}
        isfile.reset_mock()

        with mock.patch("sys.stderr.write") as write:
            assert manager.run(["single_dep"]) == 3
        assert "first dependency substitution is not supported" in get_mocked_stdout(write)
        check_call.assert_not_called()
        check_call.reset_mock()

        assert not manager.run(["multiple_dep"])
        check_call.assert_called_once()
        (args, *_), _ = check_call.call_args
        # doit uses sets for file dependencies so the order is non-deterministic.
        assert set(args.split() if shell else args) == {"dep1", "dep2"}
        check_call.reset_mock()

        assert not manager.run(["name_sub"])
        check_call.assert_called_once()
        (args, *_), _ = check_call.call_args
        assert args == _maybe_join(["echo", "hello name_sub"])
        check_call.reset_mock()


def test_subprocess_invalid_args(manager: di.Manager):
    manager(basename="task", actions=[di.SubprocessAction(74)])
    with mock.patch("sys.stderr.write") as write:
        assert manager.run() == 3
    assert "74 is not a valid command" in get_mocked_stdout(write)


def test_subprocess_shell(manager: di.Manager):
    manager(basename="task", actions=[di.SubprocessAction("echo hello > world.txt")])
    assert not manager.run()
    with open("world.txt") as fp:
        assert fp.read().strip() == "hello"


def test_subprocess_use_as_default(manager: di.Manager):
    with di.SubprocessAction.use_as_default():
        task = manager(basename="task", actions=["echo hello"])
    assert isinstance(task["actions"][0], di.SubprocessAction)


def test_subprocess_fail(manager: di.Manager):
    manager(basename="task", actions=[di.SubprocessAction("false")])
    assert manager.run() == 1


@pytest.mark.parametrize("create_target", [True, False])
@pytest.mark.parametrize("check_targets", [True, False])
def test_target_not_created(manager: di.Manager, check_targets: bool, create_target: bool):
    action = di.SubprocessAction("touch target" if create_target else "true",
                                 check_targets=check_targets)
    manager(basename="task", actions=[action], targets=["target"])
    expected = 1 if not create_target and check_targets else 0
    assert manager.run() == expected
