"""
Purpose:  Import an optional package, or fail with an install command the user can copy.
Layer:    sleng.infra
Exports:  require
Depends:  sleng.domain.errors
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

from sleng.domain.errors import DependencyError


def require(module: str, install: str | None = None) -> ModuleType:
    """Import `module`; on failure raise DependencyError naming the pip command to run."""
    try:
        return importlib.import_module(module)
    except ImportError as err:
        package = install or module
        raise DependencyError(
            f"Missing package '{module}'. Install it with the Python that runs the engine: "
            f"{sys.executable} -m pip install {package}"
        ) from err
