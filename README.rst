🎯 doit interface
=================

.. image:: https://github.com/tillahoffmann/doit_interface/actions/workflows/main.yml/badge.svg
  :target: https://github.com/tillahoffmann/doit_interface/actions/workflows/main.yml
.. image:: https://img.shields.io/pypi/v/doit_interface.svg?style=flat
   :target: https://pypi.python.org/pypi/doit_interface
.. image:: https://readthedocs.org/projects/doit-interface/badge/?version=latest
   :target: https://doit-interface.readthedocs.io/en/latest/?badge=latest

This package provides a functional interface for reducing boilerplate in :code:`dodo.py` of the `pydoit <https://pydoit.org>`__ build system. In short, all tasks are created and managed using a :class:`doit_interface.Manager`. Most :ref:`features<features>` are exposed using python context manager, e.g., grouping tasks.

Basic usage
-----------

.. doctest:: example

  >>> import doit_interface as di


  >>> # Get a default manager (or create your own to use as a context manager).
  >>> manager = di.Manager.get_instance()

  >>> # Create a single task.
  >>> manager(basename="create_foo", actions=["touch foo"], targets=["foo"])
  {'basename': 'create_foo', 'actions': ['touch foo'], 'targets': ['foo'], ...}

  >>> # Group multiple tasks.
  >>> with di.group_tasks("my_group") as my_group:
  ...     member = manager(basename="member")
  >>> my_group
  <doit_interface.contexts.group_tasks object at 0x...> named `my_group` with 1 task

.. note::

  The default manager obtained by calling :meth:`doit_interface.Manager.get_instance` has a number of default contexts enabled:

  1. :class:`doit_interface.SubprocessAction.use_as_default` to use :class:`doit_interface.SubprocessAction` by default for string actions.
  2. :class:`contexts.create_target_dirs` to create target directories if they are missing.
  3. :class:`contexts.normalize_dependencies` such that task objects can be used as file and task dependencies.

  If you want to override this default behavior, you can create a dedicated manager and call :meth:`doit_interface.Manager.set_default_instance` or modify the :attr:`doit_interface.Manager.context_stack` of the default manager.


.. _features:

Features
--------

Traceback for failed tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`DoitInterfaceReporter` provides more verbose progress reports and points you to the location where a failing task was defined.

.. doctest:: reporter

  >>> DOIT_CONFIG = {"reporter": DoitInterfaceReporter}
  >>> manager(basename="false", actions=["false"])
  {'basename': 'false', 'actions': ['false'], 'meta': {'filename': '...', 'lineno': 1}}

.. code-block:: bash

  $ doit
  EXECUTE: false
  FAILED: false (declared at ...:1)
  ...

Group tasks
^^^^^^^^^^^

Group tasks to easily execute all of them using :class:`doit_interface.group_tasks`. Tasks can be added to groups using a context manager (as shown below) or by calling the group to add an existing task. Groups can be nested arbitrarily.

.. doctest:: group_tasks

  >>> with group_tasks("vgg16") as vgg16:
  ...     train = manager(basename="train", actions=[...])
  ...     validate = manager(basename="validate", actions=[...])
  >>> vgg16
  <doit_interface.contexts.group_tasks object at 0x...> named `vgg16` with 2 tasks

Automatically create target directories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use :class:`doit_interface.create_target_dirs` to automatically create directories for each of your targets. This can be particularly useful if you generate nested data structures, e.g., for machine learning results based on different architectures, seeds, optimizers, learning rates, etc.

.. doctest:: create_target_dirs

  >>> with create_target_dirs():
  ...     task = manager(basename="bar", targets=["foo/bar"], actions=[...])
  >>> task["actions"]
  [(<function create_folder at 0x...>, ['foo']), ...]

Share default values across tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use :class:`doit_interface.defaults` to share default values across tasks, such as :code:`file_dep`.

.. doctest:: defaults

  >>> with defaults(file_dep=["data.pt"]):
  ...     train = manager(basename="train", actions=[...])
  ...     validate = manager(basename="validate", actions=[...])
  >>> train["file_dep"]
  ['data.pt']
  >>> validate["file_dep"]
  ['data.pt']

Use tasks as :code:`file_dep` or :code:`task_dep`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:class:`doit_interface.normalize_dependencies` normalizes file and task dependencies such that task objects can be used as dependencies (in addition file and task names).

.. doctest:: normalize_dependencies

  >>> with normalize_dependencies():
  ...     base_task = manager(basename="base", name="output", targets=["output.txt"])
  ...     file_dep_task = manager(basename="file_dep_task", file_dep=[base_task])
  ...     task_dep_task = manager(basename="task_dep_task", task_dep=[base_task])
  >>> file_dep_task["file_dep"]
  ['output.txt']
  >>> task_dep_task["task_dep"]
  ['base:output']

Add prefixes to paths or other attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Path prefixes can be added using the :class:`path_prefix` context if file dependencies or targets share common directories. General prefixes are also available using :class:`prefix`.

.. doctest:: path_prefix

  >>> with path_prefix(targets="outputs", file_dep="inputs"):
  ...     manager(basename="task", targets=["out.txt"], file_dep=["in1.txt", "in2.txt"])
  {'basename': 'task', 'targets': ['outputs/out.txt'], 'file_dep': ['inputs/in1.txt', 'inputs/in2.txt'], ...}

Subprocess action
^^^^^^^^^^^^^^^^^

The :class:`doit_interface.SubprocessAction` lets you spawn subprocesses akin to :class:`doit.action.CmdAction` yet with a few small differences. First, it does not capture output of the subprocess which is helpful for development but may add too much noise for deployment. Second, it supports `Makefile <https://www.gnu.org/software/make/manual/html_node/Automatic-Variables.html>`__ style variable substitutions and f-string substitutions for any attribute of the parent task. Third, it allows for global environment variables to be set that are shared across all, e.g., to limit the number of `OpenMP <https://www.openmp.org>`__ threads. You can use it by default for string-actions using the :class:`doit_interface.SubprocessAction.use_as_default` context.

Interface
---------

.. automodule:: doit_interface
  :members:
