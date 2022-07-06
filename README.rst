doit utilities
==============

.. image:: https://github.com/tillahoffmann/doit_interface/actions/workflows/main.yml/badge.svg
  :target: https://github.com/tillahoffmann/doit_interface/actions/workflows/main.yml

This package provides utilities for reducing boilerplate in :code:`dodo.py` of the `pydoit <https://pydoit.org>`__ build system. In short, all tasks are created and managed using a :class:`doit_interface.Manager`. Most functionality is exposed using python context manager, e.g., grouping tasks.

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
  group `my_group` with 1 task
  >>> # Show the task we implicitly constructed using `group_tasks`.
  >>> dict(my_group)
  {'basename': 'my_group', 'actions': [], 'task_dep': ['member'], ...}

.. testcleanup:: example

  # Need to manually clean up the instance because `doctest_global_cleanup` in `conf.py` doesn't.
  manager.clear()

Interface
---------

.. automodule:: doit_interface
  :members:
