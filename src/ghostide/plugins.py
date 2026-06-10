from __future__ import annotations

import importlib.util
import logging
from pathlib import Path

from .commands import CommandRegistry
from .config import APP_DIR


LOGGER = logging.getLogger(__name__)


def load_plugins(registry: CommandRegistry, project_root: Path) -> list[str]:
    loaded: list[str] = []
    plugin_dirs = [APP_DIR / "plugins", project_root / ".ghostide" / "plugins"]
    for plugin_dir in plugin_dirs:
        if not plugin_dir.exists():
            continue
        for plugin_file in sorted(plugin_dir.glob("*.py")):
            name = f"ghostide_plugin_{plugin_file.stem}"
            spec = importlib.util.spec_from_file_location(name, plugin_file)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                setup = getattr(module, "setup", None)
                if callable(setup):
                    setup(registry)
                    loaded.append(str(plugin_file))
            except Exception:
                LOGGER.exception("failed to load plugin %s", plugin_file)
    return loaded

