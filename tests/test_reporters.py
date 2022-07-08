import doit_interface as di
import pytest


@pytest.mark.parametrize("with_meta", [True, False])
def test_reporter(manager: di.Manager, with_meta: bool):
    task = manager(basename="false", actions=["false"])
    if not with_meta:
        task.pop("meta")
    doit_main = manager.doit_main
    doit_main.task_loader.namespace["DOIT_CONFIG"] = {
        "reporter": di.DoitInterfaceReporter,
    }
    assert doit_main.run(["false"])
