from __future__ import annotations

import subprocess
from pathlib import Path


def run_shell(command: str, cwd: Path) -> int:
    completed = subprocess.run(command, cwd=cwd, shell=True)
    return completed.returncode

