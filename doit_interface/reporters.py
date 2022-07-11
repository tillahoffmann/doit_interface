from doit.reporter import ConsoleReporter


class DoitInterfaceReporter(ConsoleReporter):
    """
    Doit console reporter that includes a traceback for failed tasks.
    """
    def _write_failure(self, result: dict, write_exception=True):
        task = result["task"]
        parts = [
            f"{result['exception'].get_name()}:",
            f"`{task.name}`",
            "defined at",
        ]
        try:
            meta = task.meta or {}
            filename = meta["filename"]
            lineno = meta["lineno"]
            parts.append(f"{filename}:{lineno}")
        except (AttributeError, KeyError):
            parts.append("<unknown>")

        msg = " ".join(parts) + "\n"
        self.write(msg)
        if write_exception:
            self.write(result['exception'].get_msg())
            self.write("\n")
