import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

log = logging.getLogger("mworks")

GENERIC = {"error": "An unexpected error occurred.", "code": "INTERNAL_ERROR"}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exc(_request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and "error" in detail:
            body: dict[str, Any] = detail
        else:
            body = {"error": "Request could not be completed.", "code": "REQUEST_ERROR"}
            if isinstance(detail, str) and len(detail) < 160:
                body["error"] = detail
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def valid_exc(_request: Request, _exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"error": "The request payload is invalid.", "code": "VALIDATION_ERROR"},
        )

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error path=%s", request.url.path)
        return JSONResponse(status_code=500, content=GENERIC)
