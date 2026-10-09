"""
Purpose:  HTTP adapter: a versioned JSON/binary API (/api/v1) plus the built web UI at "/".
Layer:    sleng.adapters.http
Exports:  create_app
Depends:  fastapi, sleng.adapters.http.app
Notes:    Interactive docs at /api/docs; schema at /api/openapi.json (the web client's contract).
"""

from sleng.adapters.http.app import create_app

__all__ = ["create_app"]
