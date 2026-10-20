"""Exceptions intentionally omit request URLs, credentials and server messages."""

from __future__ import annotations

from .models import APIResponse


class BuiltWithError(Exception):
    """Base for all SDK failures."""


class APIError(BuiltWithError):
    """HTTP or application error; response retains partial data for inspection."""

    def __init__(
        self,
        message: str,
        *,
        response: APIResponse | None = None,
        codes: tuple[int, ...] = (),
    ) -> None:
        super().__init__(message)
        self.response = response
        self.status_code = response.status_code if response else None
        self.codes = codes


class AuthenticationError(APIError):
    """Missing or rejected credentials."""


class RateLimitError(APIError):
    """HTTP 429 after the configured retry budget."""


class EntitlementError(APIError):
    """Insufficient credits or subscription access."""


class ResponseError(APIError):
    """Malformed response or unusable pagination information."""


class TransportError(BuiltWithError):
    """Network or transport failure without a usable response."""


class TimeoutError(TransportError):
    """HTTP request timed out."""
