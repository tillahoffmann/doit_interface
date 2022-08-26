from doit_interface import Manager
from doit_interface.util import NoTasksError
import pytest
from unittest import mock


def test_get_default_manager():
    assert Manager._DEFAULT_MANAGER is None
    manager = Manager.get_instance()
    assert Manager._DEFAULT_MANAGER is manager
    Manager._DEFAULT_MANAGER = None


def test_get_manager():
    with Manager() as manager:
        other = Manager.get_instance()
        assert other is manager
        assert Manager._CURRENT_MANAGER is manager
        assert Manager._DEFAULT_MANAGER is None
    assert Manager._CURRENT_MANAGER is None


def test_set_default_instance():
    instance = Manager()
    assert Manager.get_instance() is not instance
    assert Manager.set_default_instance(instance) is instance
    assert Manager.get_instance() is instance


def test_get_missing_manager_strict():
    with pytest.raises(RuntimeError):
        Manager.get_instance(strict=True)


def test_create_task(manager: Manager):
    task = manager(basename="basename")
    assert task in manager.tasks
    assert "with 1 task" in str(manager)


def test_call_context(manager: Manager):
    context = mock.Mock(side_effect=lambda x: x)
    manager.context_stack.append(context)
    task = manager(basename="basename")
    context.assert_called_once_with(task)


def test_call_context_missing_return(manager: Manager):
    with pytest.raises(ValueError):
        manager.context_stack.append(lambda x: None)
        manager()


def test_multiple_contexts_active(manager: Manager):
    with pytest.raises(RuntimeError), Manager():
        pass


def test_corrupt_manager_state():
    value = "some other value"
    with pytest.raises(RuntimeError), Manager():
        Manager._CURRENT_MANAGER = value
    assert Manager._CURRENT_MANAGER is value
    Manager._CURRENT_MANAGER = None


def test_clear(manager: Manager):
    manager(basename="task1")
    manager(basename="task2")
    manager.context_stack.append(None)
    manager.clear()
    assert not manager.tasks
    assert not manager.context_stack


def test_no_tasks(manager: Manager):
    with pytest.raises(NoTasksError):
        list(manager._create_doit_tasks())


def test_no_basename(manager: Manager):
    with pytest.raises(ValueError):
        manager()
