"""Exceptions module."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
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


class ClientInactiveError(APIError):
    """422: the saved client named by client_id was deactivated.

    `client_id` names it; Clients.reactivate() brings it back.
    """

    def __init__(self, status_code: int, detail: Any) -> None:
        super().__init__(status_code, detail)
        self.client_id: str = str(detail.get("client_id") or "")


class ClientNotFoundError(APIError):
    """404: no client of this company has that client_id."""

    def __init__(self, status_code: int, detail: Any) -> None:
        super().__init__(status_code, detail)
        self.client_id: str = str(detail.get("client_id") or "")


class ItemAlreadyExistsError(APIError):
    """409: the company already has an item with this code or external_reference.

    `item_id` names that item and `field` says which of the two collided
    (code or external_reference). A deactivated item still holds its code.
    """

    def __init__(self, status_code: int, detail: Any) -> None:
        super().__init__(status_code, detail)
        self.item_id: str = str(detail.get("item_id") or "")
        self.field: str = str(detail.get("field") or "")


class ItemNotFoundError(APIError):
    """404: no item of this company has that item_id."""

    def __init__(self, status_code: int, detail: Any) -> None:
        super().__init__(status_code, detail)
        self.item_id: str = str(detail.get("item_id") or "")


class ItemInactiveError(APIError):
    """422: the catalog item named by item_id was deactivated.

    `item_id` names it; Items.reactivate() brings it back.
    """

    def __init__(self, status_code: int, detail: Any) -> None:
        super().__init__(status_code, detail)
        self.item_id: str = str(detail.get("item_id") or "")


class ItemKindMismatchError(APIError):
    """422: a service item on an NF-e, or a product item on an NFS-e.

    `item_id` names the item and `index` the line of `items` that named it
    (None when the API does not say).
    """

    def __init__(self, status_code: int, detail: Any) -> None:
        super().__init__(status_code, detail)
        self.item_id: str = str(detail.get("item_id") or "")
        index = detail.get("index")
        self.index: int | None = index if isinstance(index, int) else None


class ItemTaxRequiredError(APIError):
    """422: the item's tax_situation needs a base and a rate it does not keep.

    Send `product.br.tax` on that line. `item_id` names the item.
    """

    def __init__(self, status_code: int, detail: Any) -> None:
        super().__init__(status_code, detail)
        self.item_id: str = str(detail.get("item_id") or "")


class PaymentRequiredError(APIError):
    """402: the account has no allowance or credit left for this call.

    `detail` says what ran out; topping up the credit is the way on.
    """


class RateLimitedError(APIError):
    """429: too many calls, or the SEFAZ's wait is not over.

    `retry_after` is the Retry-After header in seconds, `code` names the
    limit (DISTRIBUTION_COOLDOWN for the received documents' one-hour
    wait) and `retry_at` is the moment the wait ends, when the API says.
    Each is None when the response does not carry it.
    """

    def __init__(
        self,
        status_code: int,
        detail: Any,
        *,
        retry_after: int | None = None,
        retry_at: datetime | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(status_code, detail)
        self.retry_after = retry_after
        self.retry_at = retry_at
        self.code = code


class ConnectionFailedError(InvoiceError):
    """The API could not be reached at all (network/DNS/timeout)."""


def _seconds(value: Any) -> int | None:
    """A Retry-After given in seconds; the HTTP-date form is not sent."""
    try:
        return max(0, int(str(value).strip()))
    except (TypeError, ValueError):
        return None


def _moment(value: Any) -> datetime | None:
    """An ISO 8601 moment, a trailing Z read as UTC."""
    if not isinstance(value, str) or not value:
        return None
    text = value[:-1] + "+00:00" if value.endswith(("Z", "z")) else value
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment


def _rate_limited(
    status_code: int,
    detail: Any,
    body: Any,
    headers: Mapping[str, str],
) -> RateLimitedError:
    fields = body if isinstance(body, dict) else {}
    code = fields.get("code")
    if code is None and isinstance(detail, dict):
        code = detail.get("code")
    return RateLimitedError(
        status_code,
        detail,
        retry_after=_seconds(headers.get("Retry-After")),
        retry_at=_moment(fields.get("retry_at")),
        code=str(code) if code is not None else None,
    )


def _api_error(
    status_code: int,
    detail: Any,
    body: Any = None,
    headers: Mapping[str, str] | None = None,
) -> APIError:
    """The typed APIError a refusal maps to.

    `body` is the whole JSON answer and `headers` the response's, for
    what a 429 carries beside `detail`.
    """
    if status_code == 402:
        return PaymentRequiredError(status_code, detail)
    if status_code == 429:
        return _rate_limited(status_code, detail, body, headers or {})
    if isinstance(detail, dict):
        if status_code == 422 and detail.get("code") == "CLIENT_INACTIVE":
            return ClientInactiveError(status_code, detail)
        if status_code == 404 and detail.get("code") == "CLIENT_NOT_FOUND":
            return ClientNotFoundError(status_code, detail)
        if status_code == 409 and detail.get("code") == "ITEM_EXISTS":
            return ItemAlreadyExistsError(status_code, detail)
        if status_code == 404 and detail.get("code") == "ITEM_NOT_FOUND":
            return ItemNotFoundError(status_code, detail)
        if status_code == 422 and detail.get("code") == "ITEM_INACTIVE":
            return ItemInactiveError(status_code, detail)
        if status_code == 422 and detail.get("code") == "ITEM_KIND_MISMATCH":
            return ItemKindMismatchError(status_code, detail)
        if status_code == 422 and detail.get("code") == "ITEM_TAX_REQUIRED":
            return ItemTaxRequiredError(status_code, detail)
        if status_code == 422 and detail.get("error") == "company_required":
            return CompanyRequiredError(status_code, detail)
        if status_code == 403 and detail.get("error") == "company_not_in_scope":
            return CompanyNotInScopeError(status_code, detail)
        if status_code == 403 and detail.get("code") == "INSUFFICIENT_PERMISSION":
            return InsufficientPermissionError(status_code, detail)
        if status_code == 409 and detail.get("code") == "CLIENT_EXISTS":
            return ClientAlreadyExistsError(status_code, detail)
    return APIError(status_code=status_code, detail=detail)
