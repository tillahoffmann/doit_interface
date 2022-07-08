doit interface
==============

.. image:: https://github.com/tillahoffmann/doit_interface/actions/workflows/main.yml/badge.svg
  :target: https://github.com/tillahoffmann/doit_interface/actions/workflows/main.yml
.. image:: https://img.shields.io/pypi/v/doit_interface.svg?style=flat
   :target: https://pypi.python.org/pypi/doit_interface
.. image:: https://readthedocs.org/projects/doit-interface/badge/?version=latest
   :target: https://doit-interface.readthedocs.io/en/latest/?badge=latest

This package provides a functional interface for reducing boilerplate in :code:`dodo.py` of the `pydoit <https://pydoit.org>`__ build system. In short, all tasks are created and managed using a :class:`doit_interface.Manager`. Most functionality is exposed using python context manager, e.g., grouping tasks.

Example
-------

.. doctest:: example

  >>> import doit_interface as di


  >>> manager = di.Manager.get_instance()

  >>> # Create a single task.
  >>> manager(basename="create_foo", actions=["touch foo"], targets=["foo"])
  {'basename': 'create_foo', 'actions': ['touch foo'], 'targets': ['foo'], ...}

  >>> # Group multiple tasks.
  >>> with di.group_tasks("my_group") as my_group:
  ...     manager(basename="member")
  {'basename': 'member', ...}
  >>> my_group
  <doit_interface.contexts.group_tasks object at 0x...> named `my_group` with 1 task
  >>> # Show the task we implicitly constructed using `group_tasks`.
  >>> dict(my_group)
  {'basename': 'my_group', 'actions': [], 'task_dep': ['member'], ...}

Interface
---------

.. automodule:: doit_interface
  :members:
