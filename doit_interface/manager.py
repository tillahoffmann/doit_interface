from __future__ import annotations
from doit.cmd_base import NamespaceTaskLoader
from doit.doit_cmd import DoitMain
import inspect
from . import contexts
from .config import DOIT_CONFIG as _DEFAULT_DOIT_CONFIG
from .util import NoTasksError


class Manager:
    """
    Task manager.

    Args:
        context_stack: Stack of context managers that will be applied to all associated tasks.

    Attributes:
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
        Get the currently active manager instance.

        If no manager is active, a global instance is returned that includes a number of default
        contexts. Should you require a manager without default contexts, create a new one and use
        it with a :code:`with` statement or call :meth:`set_default_instance`.

        Args:
            strict: Enforce that a specific manager is active rather than relying on a default.
        """
        if cls._CURRENT_MANAGER:
            return cls._CURRENT_MANAGER
        elif strict:
            raise RuntimeError("no manager is active")
        if not cls._DEFAULT_MANAGER:
            from .actions import SubprocessAction
            cls._DEFAULT_MANAGER = Manager()
            cls._DEFAULT_MANAGER.context_stack.extend([
                SubprocessAction.use_as_default(),
                contexts.create_target_dirs(),
                contexts.normalize_dependencies(),
            ])
        cls.__maybe_inject_doit_config()
        return cls._DEFAULT_MANAGER

    @classmethod
    def set_default_instance(cls, instance: Manager) -> Manager:
        """
        Set the default manager.

        Args:
            instance: Instance to use by default.

        Returns:
            instance: Input argument.
        """
        cls._DEFAULT_MANAGER = instance
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

    def doit_main(self, DOIT_CONFIG=None, **kwargs) -> DoitMain:
        """
        Doit interface object.
        """
        loader = NamespaceTaskLoader()
        loader.namespace = {"manager": self, "DOIT_CONFIG": DOIT_CONFIG or {}, **kwargs}
        return DoitMain(loader)

    def run(self, args: list[str] = None, **kwargs) -> int:
        """
        Run doit as if called from the command line.

        Args:
            args: Command line arguments.
            **kwargs: Keyword arguments passed to :meth:`doit_main`.

        Returns:
            status: Status code of the run (see :code:`doit.doit_cmd.DoitMain.run` for details).
        """
        return self.doit_main(**kwargs).run(args or [])

    @staticmethod
    def __maybe_inject_doit_config() -> None:  # pragma: no cover
        """
        This function injects a `DOIT_CONFIG` variable into the callling module's scope if the
        filename is `dodo.py` and a `DOIT_CONFIG` variable does not yet exist.
        """
        # Walk up the call stack until we find a file named `dodo.py` or the stack ends.
        frame = inspect.currentframe()
        while frame := frame.f_back:
            if frame.f_code.co_filename.endswith("dodo.py"):
                frame.f_globals.setdefault("DOIT_CONFIG", _DEFAULT_DOIT_CONFIG)
                return
        # We didn't find the dodo file. Maybe we just imported the module from somewhere else.
