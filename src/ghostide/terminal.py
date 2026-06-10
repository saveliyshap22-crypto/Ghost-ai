from __future__ import annotations

import subprocess
from pathlib import Path


_ACTIVE: list[subprocess.Popen] = []


def run_shell(command: str, cwd: Path) -> int:
    process = subprocess.Popen(command, cwd=cwd, shell=True)
    _ACTIVE.append(process)
    try:
        return process.wait()
    finally:
        if process in _ACTIVE:
            _ACTIVE.remove(process)


def kill_children() -> None:
    """Terminate any shell commands still running (used during IDE shutdown)."""
    for process in list(_ACTIVE):
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
        if process in _ACTIVE:
            _ACTIVE.remove(process)
