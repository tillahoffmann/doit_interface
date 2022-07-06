import typing


def normalize_task_name(task: typing.Union[dict, str]) -> str:
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
    if (name := task.get("name")):
        return f"{task['basename']}:{name}"
    return task["basename"]


class NoTasksError(Exception):
    """
    No tasks have been discovered.
    """
