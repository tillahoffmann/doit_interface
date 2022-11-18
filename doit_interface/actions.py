from doit.action import BaseAction
from doit.exceptions import TaskFailed
from doit.task import Task
import os
import subprocess
import sys
from typing import Iterable, Union
from .contexts import _BaseContext


class SubprocessAction(BaseAction):
    """
    Launch a subprocess.

    This action supports substitution for the following variables:

    - :code:`$@`: first target of the corresponding task.
    - :code:`$^`: unordered list of file dependencies.
    - :code:`$!`: current python interpreter.

    Substitution of the first file dependency :code:`$<` is not currently supported because doit
    uses an unordered set for dependencies (see https://github.com/pydoit/doit/pull/430 for
    details).

    Python format string substitution is also supported with keys matching the valid attributes of
    :code:`doit.task.Task`.

    Args:
        args: Sequence of program arguments or shell command.
        env: Environment variables.
        inherit_env: Inherit the environment from the parent process. The environment is updated
            with `env` if `True` and replaced by `env` if `False`.
        check_targets: Check that targets are created.
        **kwargs: Keyword arguments passed to :func:`subprocess.check_call`.

    Example:

        >>> # Write "hello" to the first target of the task.
        >>> SubprocessAction("echo hello > $@")
        <doit_interface.actions.SubprocessAction object at 0x...>

        >>> # Write the task name to the first target of the task.
        >>> SubprocessAction("echo {name} > $@")
        <doit_interface.actions.SubprocessAction object at 0x...>
    """
    _GLOBAL_ENV = {}

    def __init__(self, args: Union[str, Iterable[str]], task: Task = None, env: dict = None,
                 inherit_env: bool = True, check_targets: bool = True, **kwargs):
        self.args = args
        self.task = task
        self.env = env or {}
        self.inherit_env = inherit_env
        self.check_targets = check_targets
        self.kwargs = kwargs
        self.err = self.out = self.result = None
        self.values = {}

    def _format_arg(self, arg: str, variables: dict):
        arg = arg.format(**variables)
        arg = arg.replace("$!", sys.executable)
        if "$@" in arg:
            if not (targets := variables.get("targets")):
                raise ValueError(f"task {self.task} does not have any targets")
            target, *_ = targets
            arg = arg.replace("$@", target)
        if "$<" in arg:
            raise ValueError(
                "first dependency substitution is not supported because doit uses unordered sets "
                "for dependencies; see https://github.com/pydoit/doit/pull/430"
            )
        return arg

    def execute(self, out=None, err=None) -> None:
        if self.inherit_env:
            env = dict(os.environ)
        else:
            env = {}
        env.update(self._GLOBAL_ENV)
        env.update(self.env)
        env = {key: str(value) for key, value in env.items() if value is not None}

        variables = {key: getattr(self.task, key) for key in self.task.valid_attr
                     if hasattr(self.task, key)}
        kwargs = dict(self.kwargs)
        if isinstance(self.args, str):
            kwargs.setdefault("shell", True)
            args = self._format_arg(self.args, variables)
            if "$^" in args:
                if not self.task.file_dep:
                    raise ValueError(f"task {self.task} does not have any file dependencies")
                args = args.replace("$^", " ".join(self.task.file_dep))
        elif isinstance(self.args, Iterable):
            kwargs.setdefault("shell", False)
            args = []
            for arg in map(str, self.args):
                arg = self._format_arg(arg, variables)
                # Apply string substitutions.
                if arg == "$^":
                    if not self.task.file_dep:
                        raise ValueError(f"task {self.task} does not have any file dependencies")
                    args.extend(self.task.file_dep)
                    continue
                args.append(arg)
        else:
            raise ValueError(f"{self.args} is not a valid command")

        try:
            subprocess.check_call(args, env=env, **kwargs)
        except Exception as ex:
            return TaskFailed(str(ex), exception=ex)

        if self.check_targets:
            for target in self.task.targets:
                if not os.path.isfile(target):
                    return TaskFailed(f"target {target} was not created")

    @classmethod
    def set_global_env(cls, env):
        r"""
        Set global environment variables for all :class:`SubprocessAction`\s.
        """
        cls._GLOBAL_ENV = env

    @classmethod
    def get_global_env(cls):
        r"""
        Get global environment variables for all :class:`SubprocessAction`\s.
        """
        return cls._GLOBAL_ENV

    class use_as_default(_BaseContext):
        """
        Use the :class:`SubprocessAction` as the default action for strings (with shell execution)
        and lists of strings (without shell execution).
        """
        def __call__(self, task: dict) -> dict:
            if actions := task.get("actions"):
                task["actions"] = [
                    SubprocessAction(action) if isinstance(action, (str, list)) else action
                    for action in actions
                ]
            return task
