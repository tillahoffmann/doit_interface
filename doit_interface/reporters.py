import colorama
from doit.reporter import ConsoleReporter
from doit.task import Task


class DoitInterfaceReporter(ConsoleReporter):
    """
    Doit console reporter that includes a traceback for failed tasks.
    """
    def _write_failure(self, result: dict, write_exception=True):
        task: Task = result["task"]
        parts = [
            f"{colorama.Fore.RED}FAILED{colorama.Style.RESET_ALL}:",
            task.title(),
        ]
        try:
            meta = task.meta or {}
            filename = meta["filename"]
            lineno = meta["lineno"]
            parts.append(f"(declared at {filename}:{lineno})")
        except (AttributeError, KeyError):
            parts.append("(declared at <unknown>)")

        msg = " ".join(parts) + "\n"
        self.write(msg)
        if write_exception:
            self.write(result['exception'].get_msg())
            self.write("\n")

    def execute_task(self, task):
        if task.actions:
            self.write(f"{colorama.Fore.YELLOW}EXECUTE{colorama.Style.RESET_ALL}: {task.title()}\n")

    def add_success(self, task):
        if task.actions:
            self.write(f"{colorama.Fore.GREEN}SUCCESS{colorama.Style.RESET_ALL}: {task.title()}\n")

    def skip_uptodate(self, task):
        self.write(f"{colorama.Fore.GREEN}UP TO DATE{colorama.Style.RESET_ALL}: {task.title()}\n")
