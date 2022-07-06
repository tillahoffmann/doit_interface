from doit.action import BaseAction
from doit.task import Task
import os
import subprocess
import sys
import typing


class SubprocessAction(BaseAction):
    """
    Launch a subprocess.

    Args:
        args: Sequence of program arguments.
        env: Environment variables.
        inherit_env: Inherit the environment from the parent process. The environment is updated
            with `env` if `True` and replaced by `env` if `False`.
        **kwargs: Keyword arguments passed to :func:`subprocess.check_call`.
    """
    _GLOBAL_ENV = {}

    def __init__(self, args: typing.Iterable[str], task: Task = None, env: dict = None,
                 inherit_env: bool = True, **kwargs):
        self.args = args
        self.task = task
        self.env = env or {}
        self.inherit_env = inherit_env
        self.kwargs = kwargs

    def execute(self, out=None, err=None) -> None:
        if self.inherit_env:
            env = dict(os.environ)
        else:
            env = {}
        env.update(self._GLOBAL_ENV)
        env.update(self.env)
        env = {key: str(value) for key, value in env.items() if value is not None}

        args = []
        for arg in map(str, self.args):
            # Apply string substitutions.
            if arg == "$^":
                if not (file_dep := self.task.file_dep):
                    raise ValueError(f"task {self.task} does not have any file dependencies")
                args.extend(file_dep)
                continue
            if arg == "$<":
                raise ValueError(
                    "first dependency substitution is not supported because doit uses unordered "
                    "sets for dependencies; see https://github.com/pydoit/doit/pull/430"
                )
            elif arg == "$!":
                arg = sys.executable
            elif arg == "$@":
                if not self.task.targets:
                    raise ValueError(f"task {self.task} does not have any targets")
                arg, *_ = self.task.targets
            args.append(arg)
        subprocess.check_call(args, env=env, **self.kwargs)

    @classmethod
    def set_global_env(cls, env):
        """
        Set global environment variables for all :class:`SubprocessAction` s.
        """
        cls._GLOBAL_ENV = env

    @classmethod
    def get_global_env(cls):
        """
        Get global environment variables for all :class:`SubprocessAction` s.
        """
        return cls._GLOBAL_ENV

    @property
    def result(self):
        return None

    @property
    def values(self):
        return {}
