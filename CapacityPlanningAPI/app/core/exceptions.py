from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        detail: str,
        *,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.detail = detail
        self.errors = errors


class NotFoundError(AppError):
    def __init__(self, resource: str, identifier: object) -> None:
        super().__init__(404, "resource_not_found", f"{resource} '{identifier}' was not found")


class ConflictError(AppError):
    def __init__(self, detail: str, code: str = "resource_conflict") -> None:
        super().__init__(409, code, detail)


class AuthorizationError(AppError):
    def __init__(self, detail: str = "You are not authorized to access this resource") -> None:
        super().__init__(403, "forbidden", detail)


class AuthenticationError(AppError):
    def __init__(self, detail: str = "A valid access token is required") -> None:
        super().__init__(401, "unauthorized", detail)


def _problem(
    request: Request,
    status_code: int,
    title: str,
    detail: str,
    code: str,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": f"https://capacity-planning.example/problems/{code}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": str(request.url.path),
        "code": code,
        "correlation_id": getattr(request.state, "correlation_id", None),
    }
    if errors:
        body["errors"] = errors
    return JSONResponse(body, status_code=status_code, media_type="application/problem+json")


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return _problem(
        request,
        exc.status_code,
        exc.code.replace("_", " ").title(),
        exc.detail,
        exc.code,
        exc.errors,
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        {"location": list(error["loc"]), "message": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]
    return _problem(
        request, 422, "Validation Error", "Request validation failed", "validation_error", errors
    )


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _problem(request, exc.status_code, "HTTP Error", str(exc.detail), "http_error")
