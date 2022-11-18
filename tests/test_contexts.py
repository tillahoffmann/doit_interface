import doit_interface as di
from doit_interface.contexts import _BaseContext
import os
import pathlib
import pytest
from unittest import mock
from .conftest import get_mocked_stdout


def test_corrupt_context_stack(manager: di.Manager):
    with pytest.raises(RuntimeError), _BaseContext() as context:
        assert context in manager.context_stack
        manager.context_stack.append("some other context")


def test_defaults(manager: di.Manager):
    with di.defaults(property="value", basename="basename"):
        task = manager(other=37)
        meta = task.pop("meta")
        assert task == {"basename": "basename", "property": "value", "other": 37}
        assert meta["filename"] == __file__
        assert "lineno" in meta


def test_empty_group(manager: di.Manager):
    with pytest.raises(di.NoTasksError), di.group_tasks("group_name"):
        pass


def test_group(manager: di.Manager):
    with di.group_tasks("group_name") as group:
        manager(basename="basename1", actions=["touch file1"])
        manager(basename="basename2", actions=["touch file2"])

    assert len(group["task_dep"]) == 2
    assert len(manager.tasks) == 3
    assert "with 2 tasks" in str(group)

    assert not manager.run()
    assert os.path.isfile("file1")
    assert os.path.isfile("file2")


def test_create_target_dirs(manager: di.Manager):
    with di.create_target_dirs():
        task = manager(basename="basename", name="bar", targets=["foo/bar"],
                       actions=["touch foo/bar"])
    assert len(task["actions"]) == 2

    assert not manager.run()
    assert os.path.isdir("foo")
    assert os.path.isfile("foo/bar")


def test_missing_target_dir(manager: di.Manager):
    manager(basename="basename", name="bar", targets=["foo/bar"], actions=["touch foo/bar"])

    with mock.patch("sys.stderr.write") as write:
        assert manager.run() == 1
    assert "No such file or directory" in get_mocked_stdout(write)
    assert not os.path.isdir("foo")


def test_path_prefix(manager: di.Manager):
    manager(basename="basename", name="input", targets=["inputs/input.txt"],
            actions=["echo hello > inputs/input.txt"])
    with di.path_prefix(targets="outputs", file_dep="inputs"):
        manager(basename="basename", name="output", targets=["output.txt"], file_dep=["input.txt"],
                actions=["cp inputs/input.txt outputs/output.txt"])

    # Manually create the directories.
    os.mkdir("inputs")
    os.mkdir("outputs")
    assert not manager.run(["outputs/output.txt"])
    with open("outputs/output.txt") as fp:
        assert fp.read().strip() == "hello"


@pytest.mark.parametrize("which", ["targets", "file_dep"])
def test_path_prefix_one_of(manager: di.Manager, which: str):
    with di.path_prefix(**{which: "some/prefix"}):
        task = manager(basename="something", targets=["targets1", "targets2"],
                       file_dep=["file_dep1", "file_dep2"])
    other = "file_dep" if which == "targets" else "targets"
    assert all(x.startswith(f"some/prefix/{which}") for x in task[which])
    assert not any(x.startswith(f"some/prefix/{which}") for x in task[other])


def test_path_prefix_missing(manager: di.Manager):
    with pytest.raises(ValueError):
        di.path_prefix()


def test_path_prefix_conflict(manager: di.Manager):
    with pytest.raises(ValueError):
        di.path_prefix("prefix", targets="target_prefix")
    with pytest.raises(ValueError):
        di.path_prefix("prefix", file_dep="dependency_prefix")
    with pytest.raises(ValueError):
        di.path_prefix("prefix", targets="target_prefix", file_dep="dependency_prefix")


def test_normalize_dependencies(manager: di.Manager):
    with di.normalize_dependencies():
        task1 = manager(basename="task1", targets=["file1"])
        task2 = manager(basename="task2", file_dep=[task1, "other"])
        task3 = manager(basename="task3", name="sub", task_dep=[task2])
        task4 = manager(basename="task4", task_dep=[task3])
        task5 = manager(basename="task5", file_dep=[pathlib.Path("file5")])

        with pytest.raises(ValueError, match="does not declare any targets"):
            manager(file_dep=[task2])

        with pytest.raises(TypeError):
            manager(file_dep=[None])

        with pytest.raises(TypeError):
            manager(task_dep=[pathlib.Path("file6")])

    assert task2["file_dep"] == ["file1", "other"]
    assert task3["task_dep"] == ["task2"]
    assert task4["task_dep"] == ["task3:sub"]
    assert task5["file_dep"] == [pathlib.Path("file5")]


def test_prefix(manager: di.Manager):
    with di.prefix(basename="prefix_", not_a_property=None):
        task = manager(basename="value")
        assert task["basename"] == "prefix_value"
        assert "not_a_property" not in task
