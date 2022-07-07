import argparse
import io
from readme_renderer import rst
from unittest import mock


def __main__(args: list[str] = None):
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    args = parser.parse_args()

    with mock.patch("setuptools.setup") as setup:
        import setup as _

    setup.assert_called_once()
    _, kwargs = setup.call_args  # noqa: F811
    warning_stream = io.StringIO()
    html = rst.render(kwargs["long_description"], warning_stream)
    if html is None:
        raise ValueError(f"render failed: {warning_stream.getvalue()}")
    with open(args.output, "w") as fp:
        fp.write(html)


if __name__ == "__main__":
    __main__()
