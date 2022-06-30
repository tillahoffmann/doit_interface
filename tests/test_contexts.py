import doit_utilities as du
from doit_utilities.contexts import _BaseContext
import os
import pytest


def test_corrupt_context_stack(manager: du.Manager):
    with pytest.raises(RuntimeError), _BaseContext() as context:
        assert context in manager.context_stack
        manager.context_stack.append("some other context")


def test_defaults(manager: du.Manager):
    with du.defaults(property="value", basename="basename"):
        task = manager(other=37)
        meta = task.pop("meta")
        assert task == {"basename": "basename", "property": "value", "other": 37}
        assert meta["filename"] == __file__
        assert "lineno" in meta


def test_empty_group(manager: du.Manager):
    with pytest.raises(du.NoTasksError), du.group_tasks("group_name"):
        pass


def test_group(manager: du.Manager, tmpwd: str):
    with du.group_tasks("group_name") as group:
        manager(basename="basename1", actions=["touch file1"])
        manager(basename="basename2", actions=["touch file2"])

    assert len(group["task_dep"]) == 2
    assert len(manager.tasks) == 3
    assert "with 2 tasks" in str(group)

    assert not manager.doit_main.run([])
    assert os.path.isfile("file1")
    assert os.path.isfile("file2")


def test_create_target_dirs(manager: du.Manager, tmpwd: str):
    with du.create_target_dirs():
        task = manager(basename="basename", name="bar", targets=["foo/bar"],
                       actions=["touch foo/bar"])
    assert len(task["actions"]) == 2

    assert not manager.doit_main.run([])
    assert os.path.isdir("foo")
    assert os.path.isfile("foo/bar")


def test_missing_target_dir(manager: du.Manager, tmpwd: str):
    manager(basename="basename", name="bar", targets=["foo/bar"], actions=["touch foo/bar"])

    assert manager.doit_main.run([])
    assert not os.path.isdir("foo")


def test_path_prefix(manager: du.Manager, tmpwd: str):
    manager(basename="basename", name="input", targets=["inputs/input.txt"],
            actions=["echo hello > inputs/input.txt"])
    with du.path_prefix(target_prefix="outputs", dependency_prefix="inputs"):
        manager(basename="basename", name="output", targets=["output.txt"], file_dep=["input.txt"],
                actions=["cp inputs/input.txt outputs/output.txt"])

    # Manually create the directories.
    os.mkdir("inputs")
    os.mkdir("outputs")
    assert not manager.doit_main.run(["outputs/output.txt"])
    with open("outputs/output.txt") as fp:
        assert fp.read().strip() == "hello"


def test_path_prefix_missing(manager: du.Manager):
    with pytest.raises(ValueError):
        du.path_prefix()


def test_path_prefix_conflict(manager: du.Manager):
    with pytest.raises(ValueError):
        du.path_prefix("prefix", target_prefix="target_prefix")
    with pytest.raises(ValueError):
        du.path_prefix("prefix", dependency_prefix="dependency_prefix")
    with pytest.raises(ValueError):
        du.path_prefix("prefix", target_prefix="target_prefix",
                       dependency_prefix="dependency_prefix")


def test_normalize_dependencies(manager: du.Manager):
    with du.normalize_dependencies():
        task1 = manager(basename="task1", targets=["file1"])
        task2 = manager(basename="task2", file_dep=[task1, "other"])
        task3 = manager(basename="task3", name="sub", task_dep=[task2])
        task4 = manager(basename="task4", task_dep=[task3])

        with pytest.raises(ValueError, match="does not declare any targets"):
            manager(file_dep=[task2])

        with pytest.raises(TypeError):
            manager(file_dep=[None])

    assert task2["file_dep"] == ["file1", "other"]
    assert task3["task_dep"] == ["task2"]
    assert task4["task_dep"] == ["task3:sub"]
