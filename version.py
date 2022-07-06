import os
import re


ref = os.environ.get("GITHUB_REF", "")
match = re.match(r"^/refs/tags/([\d\.]+)$", ref)
if match:
    version = match.group(1)
    with open("VERSION", "w") as fp:
        fp.write(version)
    print(f"wrote version {version} to VERSION file")
print(f"cannot extract version from ref {ref}")
