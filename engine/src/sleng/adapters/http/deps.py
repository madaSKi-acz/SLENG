"""
Purpose:  FastAPI dependency that hands each request the process-wide engine.
Layer:    sleng.adapters.http
Exports:  EngineDep, get_engine
Depends:  fastapi, sleng.container
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from sleng.container import Sleng


def get_engine(request: Request) -> Sleng:
    engine: Sleng = request.app.state.engine
    return engine


EngineDep = Annotated[Sleng, Depends(get_engine)]
