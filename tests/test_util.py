import doit_interface as di
import pytest


@pytest.mark.parametrize("task, expected", [
    ("name", "name"),
    ({"basename": "base"}, "base"),
    ({"basename": "base", "name": "sub"}, "base:sub"),
])
def test_normalize_task_name(task, expected):
    assert di.util.normalize_task_name(task) == expected
