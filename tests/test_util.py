import doit_utilities as du
import pytest


@pytest.mark.parametrize("task, expected", [
    ("name", "name"),
    ({"basename": "base"}, "base"),
    ({"basename": "base", "name": "sub"}, "base:sub"),
])
def test_normalize_task_name(task, expected):
    assert du.util.normalize_task_name(task) == expected
