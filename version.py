import os
import re


ref = os.environ.get("GITHUB_REF", "")
match = re.match(r"^/refs/tag/([\d\.]+)$", ref)
if match:
    with open("VERSION", "w") as fp:
        fp.write(match.group(1))
