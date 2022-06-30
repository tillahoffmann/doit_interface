from __future__ import annotations
from doit.tools import create_folder
import os
from . import manager as manager_
from .util import normalize_task_name, NoTasksError


class _BaseContext:
    """
    Base class for contexts that can modify tasks. Inheriting classes should override
    :code:`__call__` to modify tasks.
    """
    def __init__(self, *, manager: "manager_.Manager" = None) -> None:
        self.manager = manager or manager_.Manager.get_instance()

    def __enter__(self):
        self.manager.context_stack.append(self)
        return self

    def __exit__(self, *_) -> None:
        if (other := self.manager.context_stack.pop()) is not self:
            raise RuntimeError(f"context stack is corrupted; another context {other} is on the "
                               "stack")

    def __call__(self, task: dict) -> dict:
        raise NotImplementedError


class normalize_dependencies(_BaseContext):
    """
    Normalize task and file dependencies. For task dependencies (`task_dep`), tasks are replaced by
    fully qualified task names. For file dependencies (`task_dep`), tasks are replaced by their
    targets.

    Example:

        >>> task1 = manager(basename="task1", name="name")
        >>> task2 = manager(basename="task2", targets=["file2.txt"])
        >>> with normalize_dependencies():
        ...     manager(basename="task3", task_dep=[task1], file_dep=[task2])
        {'basename': 'task3', 'task_dep': ['task1:name'], 'file_dep': ['file2.txt'], ...}
    """
    def __call__(self, task: dict) -> dict:
        if task_dep := task.get("task_dep"):
            task["task_dep"] = [normalize_task_name(task) for task in task_dep]
        if file_dep := task.get("file_dep"):
            transformed = []
            for dep in file_dep:
                if isinstance(dep, str):
                    transformed.append(dep)
                elif isinstance(dep, dict):
                    if targets := dep.get("targets"):
                        transformed.extend(targets)
                    else:
                        raise ValueError(f"task {normalize_task_name(dep)} does not declare any "
                                         "targets")
                else:
                    raise TypeError(dep)
            task["file_dep"] = transformed
        return task


class defaults(_BaseContext):
    """
    Apply default task properties.

    Args:
        **defaults: Default properties as keyword arguments.

    Example:
        Ensure all tasks within the :code:`defaults` context share the same basename.

        >>> with defaults(basename="basename") as d:
        ...     manager(name="task1")
        ...     manager(name="task2")
        {'basename': 'basename', 'name': 'task1', ...}
        {'basename': 'basename', 'name': 'task2', ...}
    """
    def __init__(self, *, manager: "manager_.Manager" = None, **defaults):
        super().__init__(manager=manager)
        self.defaults = defaults

    def __call__(self, task: dict) -> dict:
        return self.defaults | task


class create_target_dirs(_BaseContext):
    """
    Create parent directories for all targets.

    Example:

        >>> with create_target_dirs():
        ...     manager(basename="task", targets=["missing/directories/output.txt"])
        {'basename': 'task',
         'targets': ['missing/directories/output.txt'],
         'actions': [(<function create_folder at 0x...>, ['missing/directories'])],
         ...}
    """
    def __call__(self, task: dict) -> dict:
        # Prepend actions to create parent directories of all targets.
        actions = [(create_folder, [basename]) for target in task.get("targets", [])
                   if (basename := os.path.dirname(target))]
        task["actions"] = actions + task.get("actions", [])
        return task


class path_prefix(_BaseContext):
    """
    Add a prefix for targets and/or file dependencies.

    Args:
        prefix: Prefix for both targets and dependencies.
        target_prefix: Prefix for targets.
        dependency_prefix: Prefix for dependencies.

    Example:

        >>> with path_prefix(target_prefix="outputs", dependency_prefix="inputs"):
        ...     manager(basename="task", targets=["out.txt"], file_dep=["in.txt"])
        {'basename': 'task', 'targets': ['outputs/out.txt'], 'file_dep': ['inputs/in.txt'], ...}
    """
    def __init__(self, prefix: str = None, *, target_prefix: str = None,
                 dependency_prefix: str = None, manager: "manager_.Manager" = None):
        super().__init__(manager=manager)
        if not any([prefix, target_prefix, dependency_prefix]):
            raise ValueError("at least one of `prefix`, `target_prefix`, or `dependency_prefix` "
                             "must be given")
        if prefix and any([target_prefix, dependency_prefix]):
            raise ValueError("use either `prefix` or a combination of `target_prefix` and "
                             "`dependency_prefix` but not both")
        self.target_prefix = target_prefix or prefix
        self.dependency_prefix = dependency_prefix or prefix

    def __call__(self, task: dict) -> dict:
        if self.target_prefix and (targets := task.get("targets")):
            task["targets"] = [os.path.join(self.target_prefix, target) for target in targets]
        if self.dependency_prefix and (dependencies := task.get("file_dep")):
            task["file_dep"] = [os.path.join(self.dependency_prefix, dependency) for dependency
                                in dependencies]
        return task


class group_tasks(dict, _BaseContext):
    """
    Group of tasks.

    Args:
        basename: Basename of the task aggregating all constituent tasks.
        actions: Actions to be performed as part of this group.
        task_dep: Further task dependencies in addition to the constituent tasks.
        manager: Task manager (defaults to :code:`Manager.get_instance()`).

    Example:

        >>> with group_tasks("my_group") as group:
        ...     manager(basename="my_first_task")
        ...     manager(basename="my_second_task")
        {'basename': 'my_first_task', ...}
        {'basename': 'my_second_task', ...}
        >>> group
        group `my_group` with 2 tasks
    """
    def __init__(self, basename: str, *, actions: list = None, task_dep: list = None,
                 manager: "manager_.Manager" = None, **kwargs) -> None:
        dict.__init__(self, basename=basename, actions=actions or [], task_dep=task_dep or [],
                      **kwargs)
        _BaseContext.__init__(self, manager=manager)

        # Automatically add the group to the manager.
        self.manager(self)

    def __exit__(self, *_) -> None:
        super().__exit__(*_)
        if not self["task_dep"]:
            raise NoTasksError(f"group {self['basename']} must contain at least one task")

    def __call__(self, task: dict) -> dict:
        self["task_dep"].append(normalize_task_name(task))
        return task

    def __repr__(self) -> str:
        num_tasks = len(self['task_dep'])
        return f"group `{normalize_task_name(self)}` with {num_tasks} " \
            f"{'tasks' if num_tasks > 1 else 'task'}"
