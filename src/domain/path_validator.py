"""Centralized path containment validator.

Ensures file paths resolve within allowed directory boundaries,
preventing path traversal attacks.
"""

import logging
from pathlib import Path

from src.exceptions import PathTraversalError

logger = logging.getLogger(__name__)


def validate_path_within(path: str | Path, base_dir: str | Path) -> Path:
    """Validate that *path* resolves to a location under *base_dir*.

    Parameters
    ----------
    path:
        Relative or absolute path to validate.
    base_dir:
        Allowed root directory. Both *path* (joined to *base_dir* when
        relative) and *base_dir* are resolved to real paths before the
        containment check.

    Returns
    -------
    Path
        The fully resolved path when it is within *base_dir*.

    Raises
    ------
    PathTraversalError
        When the resolved path escapes *base_dir*.  The exception message
        is intentionally generic to avoid leaking directory structure.
    """
    base = Path(base_dir).resolve(strict=False)
    target = Path(path)

    # Join relative paths to base_dir; absolute paths resolve on their own
    if not target.is_absolute():
        resolved = (base / target).resolve(strict=False)
    else:
        resolved = target.resolve(strict=False)

    if not resolved.is_relative_to(base):
        logger.warning(
            "Path traversal blocked: %r not under %r",
            str(resolved),
            str(base),
        )
        raise PathTraversalError("Path escapes allowed directory")

    return resolved
