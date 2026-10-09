"""
Purpose:  Map engine errors to HTTP statuses with one JSON shape: {"error": str, "type": str}.
Layer:    sleng.adapters.http
Exports:  install_error_handlers, STATUS_BY_ERROR
Depends:  fastapi, sleng.domain.errors
Notes:    SlengError messages are meant for users and are returned as-is. Anything unexpected is
          logged with its traceback and answered with a generic 500 (no internals leak out).
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from sleng.domain.errors import (
    ConflictError,
    DependencyError,
    ExternalServiceError,
    InvalidInputError,
    NotFoundError,
    SlengError,
)

log = logging.getLogger(__name__)
STATUS_BY_ERROR: tuple[tuple[type[SlengError], int], ...] = (
    (InvalidInputError, 400),
    (NotFoundError, 404),
    (ConflictError, 409),
    (ExternalServiceError, 502),
    (DependencyError, 503),
)


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(SlengError, _engine_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(Exception, _unexpected_error)


def _body(message: str, kind: str, status: int) -> JSONResponse:
    return JSONResponse({"error": message, "type": kind}, status_code=status)


async def _engine_error(_: Request, exc: Exception) -> JSONResponse:
    status = next((code for kind, code in STATUS_BY_ERROR if isinstance(exc, kind)), 500)
    return _body(str(exc), type(exc).__name__, status)


async def _validation_error(_: Request, exc: Exception) -> JSONResponse:
    errors = exc.errors() if isinstance(exc, RequestValidationError) else []
    first = errors[0] if errors else {}
    where = ".".join(str(part) for part in first.get("loc", ()) if part != "body")
    message = f"{where}: {first.get('msg', 'invalid request')}" if where else "Invalid request."
    return _body(message, "ValidationError", 422)


async def _unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    log.error("Unhandled error", exc_info=exc)
    return _body("Internal error. See the engine log.", "InternalError", 500)
