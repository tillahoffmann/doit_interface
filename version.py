import os
import re


def __main__():
    try:
        ref = os.environ["GITHUB_REF"]
    except KeyError:
        print("GITHUB_REF environment variable is not defined")
        return

    match = re.match(r"^refs/tags/(\d+\.\d+\.\d+)$", ref)
    if match:
        version = match.group(1)
        with open("VERSION", "w") as fp:
            fp.write(version)
        print(f"wrote version {version} to VERSION file")
    else:
        raise ValueError(f"cannot extract version from ref {ref}")


if __name__ == "__main__":
    __main__()
