"""Exceptions module."""

from __future__ import annotations

from typing import Any


class InvoiceError(Exception):
    """Base exception for the invoice SDK."""


class APIError(InvoiceError):
    """Raised when the invoice API responds with an error status."""

    def __init__(self, status_code: int, detail: Any) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"[{status_code}] {detail}")


class CompanyRequiredError(APIError):
    """422: the credential covers several companies and none was named.

    `companies` lists the ones it covers; pass one of their `company_id`
    or `tax_id` as `company`.
    """

    def __init__(self, status_code: int, detail: Any) -> None:
        super().__init__(status_code, detail)
        self.companies: list[dict] = list(detail.get("companies") or [])


class CompanyNotInScopeError(APIError):
    """403: the named company is not one this credential covers.

    `companies` lists the ones it does cover.
    """

    def __init__(self, status_code: int, detail: Any) -> None:
        super().__init__(status_code, detail)
        self.companies: list[dict] = list(detail.get("companies") or [])


class InsufficientPermissionError(APIError):
    """403: the credential reaches the company but lacks the permission.

    `description` reads `needs X, has Y, company=<id>`.
    """

    def __init__(self, status_code: int, detail: Any) -> None:
        super().__init__(status_code, detail)
        self.description: str = str(detail.get("error_description") or "")


class ClientAlreadyExistsError(APIError):
    """409: the company already has a client with this tax_id or foreign_id.

    `client_id` names that client, to read or reactivate it instead of
    searching for it.
    """

    def __init__(self, status_code: int, detail: Any) -> None:
        super().__init__(status_code, detail)
        self.client_id: str = str(detail.get("client_id") or "")


class ConnectionFailedError(InvoiceError):
    """The API could not be reached at all (network/DNS/timeout)."""


def _api_error(status_code: int, detail: Any) -> APIError:
    """The typed APIError a company, permission or client refusal maps to."""
    if isinstance(detail, dict):
        if status_code == 422 and detail.get("error") == "company_required":
            return CompanyRequiredError(status_code, detail)
        if status_code == 403 and detail.get("error") == "company_not_in_scope":
            return CompanyNotInScopeError(status_code, detail)
        if status_code == 403 and detail.get("code") == "INSUFFICIENT_PERMISSION":
            return InsufficientPermissionError(status_code, detail)
        if status_code == 409 and detail.get("code") == "CLIENT_EXISTS":
            return ClientAlreadyExistsError(status_code, detail)
    return APIError(status_code=status_code, detail=detail)
