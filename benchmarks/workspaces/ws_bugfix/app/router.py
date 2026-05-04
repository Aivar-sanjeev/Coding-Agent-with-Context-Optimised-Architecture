"""Tiny in-memory router for tests."""

from . import auth
from .middleware import apply


def handle(path: str, headers: dict[str, str]) -> int:
    shaped = apply(headers)
    if path == "/api/ping":
        return 200 if auth.validate(shaped) else 401
    return 404
