"""
Purpose:  Package entry point: the version and the lazily imported `Sleng` facade.
Layer:    sleng (root)
Exports:  Sleng, __version__
Depends:  sleng.container (imported on first access so `import sleng.text` stays light)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

__version__ = "0.2.0"
__all__ = ["Sleng", "__version__"]

if TYPE_CHECKING:
    from sleng.container import Sleng


def __getattr__(name: str) -> Any:
    if name == "Sleng":
        from sleng.container import Sleng

        return Sleng
    raise AttributeError(f"module 'sleng' has no attribute {name!r}")
