from __future__ import annotations
from doit.cmd_base import NamespaceTaskLoader
from doit.doit_cmd import DoitMain
import inspect
from . import contexts
from .util import NoTasksError


class Manager:
    """
    Task manager.

    Args:
        context_stack: Stack of context managers that will be applied to all associated tasks.

    Example:
        Get the default manager and create a single task.

        >>> manager = Manager.get_instance()
        >>> manager(basename="my_task", actions=[lambda: print("hello world")])
        {'basename': 'my_task', 'actions': [<function <lambda> at 0x...>], ...}
        >>> manager
        <doit_interface.manager.Manager object at 0x...> with 1 task
    """
    _DEFAULT_MANAGER: Manager = None
    _CURRENT_MANAGER: Manager = None

    def __init__(self, context_stack: list["contexts._BaseContext"] = None) -> None:
        # We assign this attribute late because doit will otherwise try to discover tasks at the
        # class level.
        self.create_doit_tasks = self._create_doit_tasks

        self.tasks = []
        self.context_stack = context_stack or []

    def __call__(self, task=None, **kwargs: dict) -> dict:
        task = task or kwargs
        for context in reversed(self.context_stack):
            task = context(task)
            if task is None:
                raise ValueError(f"{context} context did not return a task but `None`")
        # Store where this task was declared.
        meta = task.setdefault("meta", {})
        parent = inspect.currentframe().f_back
        meta.update({
            "filename": parent.f_code.co_filename,
            "lineno": parent.f_lineno,
        })
        if not task.get("basename"):
            raise ValueError(
                "task declared at {filename}:{lineno} is missing a basename".format(**meta))
        self.tasks.append(task)
        return task

    def __enter__(self) -> Manager:
        if (other := self.__class__._CURRENT_MANAGER):
            raise RuntimeError(f"another manager {other} is already active")
        self.__class__._CURRENT_MANAGER = self
        return self

    def __exit__(self, *_) -> None:
        if (other := self.__class__._CURRENT_MANAGER) is not self:
            raise RuntimeError(f"manager state is corrupted: another manager {other} is active")
        self.__class__._CURRENT_MANAGER = None

    def _create_doit_tasks(self):
        if not self.tasks:
            raise NoTasksError("task manager must have at least one task")
        for task in self.tasks:
            yield dict(task)

    @classmethod
    def get_instance(cls, strict: bool = False) -> Manager:
        """
        Get the global default manager.

        Args:
            strict: Enforce that a specific manager is active rather than relying on a default.
        """
        if cls._CURRENT_MANAGER:
            return cls._CURRENT_MANAGER
        elif strict:
            raise RuntimeError("no manager is active")
        if not cls._DEFAULT_MANAGER:
            cls._DEFAULT_MANAGER = Manager()
        return cls._DEFAULT_MANAGER

    def __repr__(self) -> str:
        return f"{super().__repr__()} with {len(self.tasks)} " \
            f"{'tasks' if len(self.tasks) > 1 else 'task'}"

    def clear(self):
        """
        Reset the state of the manager.
        """
        self.tasks.clear()
        self.context_stack.clear()

    @property
    def doit_main(self) -> DoitMain:
        """
        Doit interface object.
        """
        loader = NamespaceTaskLoader()
        loader.namespace = {"manager": self}
        return DoitMain(loader)
