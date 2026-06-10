from __future__ import annotations

import logging

from .terminal import kill_children

LOGGER = logging.getLogger(__name__)


def shutdown_everything(app) -> None:
    """Release the local model and terminate spawned child processes."""
    context = getattr(app, "context", None)
    if context is not None and getattr(context, "ai", None) is not None:
        try:
            context.ai.close()
        except Exception:
            LOGGER.exception("failed to unload local model")
    kill_children()

