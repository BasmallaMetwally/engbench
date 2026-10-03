import json
import re
import shlex
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dockerfiles_do_not_leak_grader_or_reference():
    for dockerfile in (ROOT / "tasks").glob("*/Dockerfile"):
        for line in dockerfile.read_text().splitlines():
            match = re.match(r"^\s*(COPY|ADD)\s+(.+)$", line, re.IGNORECASE)
            if not match:
                continue

            _, payload = match.groups()
            assert not re.search(r"\b(grader|reference)\b", line, re.IGNORECASE), (
                f"{dockerfile}: leaks protected task files: {line}"
            )
            if payload.lstrip().startswith("["):
                paths = json.loads(payload)
                sources = paths[:-1]
            else:
                fields = shlex.split(payload)
                while fields and fields[0].startswith("--"):
                    fields.pop(0)
                sources = fields[:-1]

            whole_directory = [source for source in sources if source in {".", "./"}]
            assert not whole_directory, f"{dockerfile}: copies whole directory: {line}"
