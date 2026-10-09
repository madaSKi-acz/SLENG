"""
Purpose:  Every API router, in the order they appear in the docs.
Layer:    sleng.adapters.http.routes
Exports:  ROUTERS
Depends:  sleng.adapters.http.routes.{meta, voices, speech, exports, jobs}
"""

from sleng.adapters.http.routes import exports, jobs, meta, speech, voices

ROUTERS = (meta.router, voices.router, speech.router, exports.router, jobs.router)

__all__ = ["ROUTERS"]
