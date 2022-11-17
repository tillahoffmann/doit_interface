from typing import Union


def normalize_task_name(task: Union[dict, str]) -> str:
    """
    Get the fully qualified task name.

    Args:
        task: Task whose name to normalize.

    Returns:
        normalized_task_name: Fully qualified task name.

    Example:

        >>> normalize_task_name({"basename": "basename"})
        'basename'
        >>> normalize_task_name({"basename": "basename", "name": "name"})
        'basename:name'
    """
    if isinstance(task, str):
        return task
    if not isinstance(task, dict):
        raise TypeError(f"{task} of type {type(task)} is not a valid task or task name")
    if name := task.get("name"):
        return f"{task['basename']}:{name}"
    return task["basename"]


class NoTasksError(Exception):
    """
    No tasks have been discovered.
    """


def dict2args(*args, **kwargs):
    """
    Convert a dictionary of values to named command line arguments.

    Args:
        *args: Sequence of mappings to convert.
        **kwargs: Keyword arguments to convert.

    Returns:
        args: Sequence of named command line arguments.

    Example:

        >>> dict2args({"hello": "world"}, foo="bar")
        ['--hello=world', '--foo=bar']
    """
    result = {}
    values = list(args) + [kwargs]
    for kwargs in values:
        for key, value in kwargs.items():
            if key in result:
                raise ValueError(f"key {key} is supplied twice")
            result[key] = value
    return [f"--{key}={value}" for key, value in result.items()]
