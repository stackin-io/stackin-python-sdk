"""Client module"""

from __future__ import annotations

import os
import re
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, cast

import requests

from stackin.br.export import Export
from stackin.br.product import Product
from stackin.core.address import Address
from stackin.core.exceptions import APIError, ConnectionFailedError
from stackin.core.types import (
    Direction,
    DocumentType,
    Environment,
    Manifestation,
    Purpose,
)

DEFAULT_BASE_URL = "https://sdk.stackin.io"

_ENVIRONMENT_URLS = {
    Environment.LOCAL: "http://localhost:8000",
    Environment.TEST: DEFAULT_BASE_URL,
    Environment.PRODUCTION: DEFAULT_BASE_URL,
}


def _resolve_base_url(
    base_url: str | None, environment: Environment | str | None
) -> str:
    """Explicit param, then env var, then the environment's default."""
    if base_url:
        return base_url
    if url := os.environ.get("STACKIN_BASE_URL"):
        return url

    if environment is not None:
        return _ENVIRONMENT_URLS[Environment(environment)]
    if env_name := os.environ.get("STACKIN_ENVIRONMENT"):
        return _ENVIRONMENT_URLS[Environment(env_name)]
    return DEFAULT_BASE_URL


_NFE_DESCRIPTION_MAX = 120

# cUF+AAMM, then the issuer CNPJ (alphanumeric from July 2026: letters
# in its first 12 positions), then the rest. Same check as the API's.
_NFE_ACCESS_KEY = re.compile(r"[0-9]{6}[0-9A-Z]{12}[0-9]{26}")

_NFE_ADDRESS_FIELDS = (
    "street",
    "number",
    "neighborhood",
    "city",
    "state",
    "zip_code",
)


_NFE_ABROAD_ADDRESS_FIELDS = (
    "street",
    "number",
    "neighborhood",
    "city",
    "state",
    "country_code",
)

_ABROAD_STATE = "EX"


def _is_abroad(address: Address | None) -> bool:
    """State EX is a buyer outside Brazil."""
    return address is not None and (address.state or "").upper() == _ABROAD_STATE


def _validate_nfe_address(address: Address | None) -> None:
    """NFE needs the full address — a partial one the SEFAZ rejects.

    A buyer abroad (state EX) has no CEP, so zip_code may be left out
    there; the country it names is then required instead.
    """
    if address is None:
        raise ValueError("recipient_address is required for NFE")

    required = (
        _NFE_ABROAD_ADDRESS_FIELDS if _is_abroad(address) else _NFE_ADDRESS_FIELDS
    )
    missing = [field for field in required if not getattr(address, field)]
    if missing:
        raise ValueError(
            "recipient_address is missing required fields for NFE: "
            + ", ".join(missing)
        )


# What the API converts before its own latin1 check (stackin-api#228):
# typographic quotes, dashes, ellipsis, bullet, euro and trademark.
# Those are not refused here; the SDK does not translate them either.
_API_CONVERTED = frozenset(
    "\u2018\u2019\u201a\u201c\u201d\u201e\u2013\u2014\u2212\u2026\u2022\u20ac\u2122"
)


def _first_non_latin1(value: Any, path: str) -> tuple[str, str] | None:
    """The first character in `value` the NF-e cannot carry, with its path.

    Anything up to U+00FF passes (tab, newline and CR included: the API
    folds them into a space), and so does what the API converts.
    """
    if isinstance(value, str):
        for char in value:
            if char > "\u00ff" and char not in _API_CONVERTED:
                return path, char
        return None
    if isinstance(value, dict):
        for key, nested in value.items():
            child = f"{path}.{key}" if path else str(key)
            if found := _first_non_latin1(nested, child):
                return found
        return None
    if isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            if found := _first_non_latin1(nested, f"{path}[{index}]"):
                return found
    return None


def _validate_nfe_latin1(payload: dict) -> None:
    """NF-e is encoded in ISO-8859-1; the SEFAZ refuses anything else.

    Walks every string the request would carry, so a free-text field
    added later is covered without being listed here. Refuses only what
    the API would refuse after its own normalisation, never more.
    """
    if found := _first_non_latin1(payload, ""):
        path, char = found
        raise ValueError(
            f"{path} contains a character outside ISO-8859-1 (latin1), "
            f"which NF-e does not accept: '{char}'"
        )


_NFSE_RETAINED_ADDRESS_FIELDS = _NFE_ADDRESS_FIELDS


def _discount_str(discount: Decimal | int | float | str) -> str:
    """The document discount as a decimal string, like the item amounts."""
    try:
        value = discount if isinstance(discount, Decimal) else Decimal(str(discount))
    except InvalidOperation as error:
        raise ValueError(f"discount must be a number, not {discount!r}") from error
    if not value.is_finite() or value < 0:
        raise ValueError("discount must be zero or more")
    return format(value, "f")


def _issued_at_str(issued_at: datetime) -> str:
    """ISO 8601 with the offset; a naive value has no moment to send."""
    if not isinstance(issued_at, datetime):
        raise ValueError("issued_at must be a datetime")
    if issued_at.utcoffset() is None:
        raise ValueError(
            "issued_at must be timezone-aware: a naive datetime does not "
            "say which moment it is"
        )
    return issued_at.isoformat()


def _referenced_keys_list(referenced_keys: Sequence[str]) -> list[str]:
    """A bare string would be sent one character per key."""
    if isinstance(referenced_keys, str) or not all(
        isinstance(key, str) for key in referenced_keys
    ):
        raise ValueError("referenced_keys must be a list of access keys")
    return list(referenced_keys)


def _validate_nfse_retained_address(address: Address | None) -> None:
    """Retained ISSQN needs the tomador's address — the authorizer refuses
    the document without it (E0237). Every field but city_code."""
    if address is None:
        raise ValueError(
            "recipient_address is required on an NFS-e when any item "
            "has tax_retained=true (ISSQN retained by the tomador)"
        )

    missing = [
        field for field in _NFSE_RETAINED_ADDRESS_FIELDS if not getattr(address, field)
    ]
    if missing:
        raise ValueError(
            "recipient_address is missing required fields for NFSE with "
            "tax_retained=true: " + ", ".join(missing)
        )


class _Client:
    """Where an api_key becomes an HTTP call, for every entry point.

    Lives here rather than in a module of its own because the tests
    patch `stackin.core.client.requests`, and so every request the SDK
    makes has to be issued from this module.
    """

    def __init__(
        self,
        base_url: str | None = None,
        environment: Environment | str | None = None,
        api_key: str | None = None,
        timeout: int = 30,
    ) -> None:
        resolved_url = _resolve_base_url(base_url, environment)
        self.base_url = resolved_url.rstrip("/")
        self.api_key = api_key or os.environ.get("STACKIN_API_KEY")
        self.timeout = timeout

    def _headers(self, idempotency_key: str | None = None) -> dict:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        idempotency_key: str | None = None,
    ) -> Any:
        response = self._send(
            method,
            path,
            json=json,
            params=params,
            idempotency_key=idempotency_key,
        )
        try:
            body = response.json() if response.content else {}
        except ValueError:
            body = {}
        if isinstance(body, dict):
            return body.get("result", body)
        return body

    def _send(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        idempotency_key: str | None = None,
    ) -> requests.Response:
        url = f"{self.base_url}/api/v1{path}"

        try:
            response = requests.request(
                method,
                url,
                json=json,
                params=params,
                headers=self._headers(idempotency_key),
                timeout=self.timeout,
            )
        except requests.RequestException as error:
            raise ConnectionFailedError(str(error)) from error

        if not response.ok:
            try:
                body = response.json() if response.content else {}
            except ValueError:
                body = {}
            raise APIError(
                status_code=response.status_code,
                detail=body.get("detail", response.text),
            )

        return response


class Invoice(_Client):
    """Client for issuing, consulting, and cancelling fiscal documents."""

    def issue(
        self,
        *,
        document_type: DocumentType,
        client_name: str,
        tax_id: str | None = None,
        items: list[Product],
        recipient_address: Address | None = None,
        series: str | None = None,
        number: str | None = None,
        external_reference: str | None = None,
        idempotency_key: str | None = None,
        discount: Decimal | None = None,
        issued_at: datetime | None = None,
        purpose: Purpose | None = None,
        direction: Direction | None = None,
        referenced_keys: list[str] | None = None,
        foreign_id: str | None = None,
        export: Export | None = None,
    ) -> dict:
        """Issues a fiscal document.

        `city_code` may be left off the address: the API resolves the
        IBGE code from city and state. `external_reference` is the
        caller's own id for the document, an order number say, returned
        on every read and webhook. It never reaches the XML, so the
        Latin-1 check does not apply to it.

        `tax_id` is required, except on an NF-e to a buyer abroad
        (`recipient_address.state` EX), who is identified by
        `foreign_id` instead and whose goods leave through `export`.
        `discount` is spread by the API over the lines. `issued_at` must
        be timezone-aware. `purpose`, `direction` and `referenced_keys`
        are NF-e only. Each of these is left out of the body when unset;
        the fiscal rules on them are the API's, answered as an APIError.
        """
        if not items:
            raise ValueError("items can't be empty")

        abroad = document_type is DocumentType.NFE and _is_abroad(recipient_address)
        if tax_id is None and not abroad:
            raise ValueError(
                "tax_id is required, except on an NF-e to a buyer abroad "
                "(recipient_address.state EX)"
            )

        if document_type is DocumentType.NFE:
            for index, item in enumerate(items):
                if len(item.description) > _NFE_DESCRIPTION_MAX:
                    raise ValueError(
                        f"items[{index}].description exceeds "
                        f"{_NFE_DESCRIPTION_MAX} characters (NF-e xProd limit)"
                    )
                if not item.ncm:
                    raise ValueError(f"items[{index}].ncm is required for NFE")
                if not item.cfop:
                    raise ValueError(f"items[{index}].cfop is required for NFE")
            _validate_nfe_address(recipient_address)
        retained = any(item.tax_retained for item in items)
        if document_type is DocumentType.NFSE and retained:
            _validate_nfse_retained_address(recipient_address)

        payload: dict[str, Any] = {
            "document_type": document_type.value,
            "client_name": client_name,
        }
        if tax_id is not None:
            payload["tax_id"] = tax_id
        payload["items"] = [item.to_dict() for item in items]
        if recipient_address:
            payload["recipient_address"] = recipient_address.to_dict()
        if series:
            payload["series"] = series
        if number:
            payload["number"] = number
        if export is not None:
            payload["export"] = export.to_dict()
        if document_type is DocumentType.NFE:
            _validate_nfe_latin1(payload)
        if external_reference:
            payload["external_reference"] = external_reference
        if discount is not None:
            payload["discount"] = _discount_str(discount)
        if issued_at is not None:
            payload["issued_at"] = _issued_at_str(issued_at)
        if purpose is not None:
            payload["purpose"] = Purpose(purpose).value
        if direction is not None:
            payload["direction"] = Direction(direction).value
        if referenced_keys is not None:
            payload["referenced_keys"] = _referenced_keys_list(referenced_keys)
        if foreign_id is not None:
            payload["foreign_id"] = foreign_id

        return cast(
            dict,
            self._request(
                "POST",
                "/invoices",
                json=payload,
                idempotency_key=idempotency_key,
            ),
        )

    def consult(
        self,
        access_key: str,
        *,
        document_type: DocumentType,
    ) -> dict:
        """Consults a fiscal document by its access key."""
        params = {"document_type": document_type.value}

        return cast(
            dict, self._request("GET", f"/invoices/{access_key}", params=params)
        )

    def cancel(
        self,
        access_key: str,
        *,
        document_type: DocumentType,
        reason: str,
        idempotency_key: str | None = None,
    ) -> dict:
        """Cancels a fiscal document by its access key.

        Repeating the same idempotency_key with the same body replays
        the first answer instead of cancelling twice. Cancelling is
        irreversible and has a legal window, so a blind retry on a
        dropped connection is the case this exists for.
        """
        payload = {
            "document_type": document_type.value,
            "reason": reason,
        }

        return cast(
            dict,
            self._request(
                "POST",
                f"/invoices/{access_key}/cancel",
                json=payload,
                idempotency_key=idempotency_key,
            ),
        )

    def invalidate(
        self,
        *,
        series: str,
        number_start: int,
        number_end: int,
        reason: str,
    ) -> dict:
        """Reports a reserved but never used NFE numbering range."""
        if not 15 <= len(reason) <= 255:
            raise ValueError("reason must be 15 to 255 characters")
        if number_end < number_start:
            raise ValueError("number_end can't be below number_start")

        payload = {
            "series": series,
            "number_start": number_start,
            "number_end": number_end,
            "reason": reason,
        }

        return cast(
            dict, self._request("POST", "/invoices/invalidations", json=payload)
        )

    def correct(
        self,
        access_key: str,
        *,
        document_type: DocumentType,
        correction: str,
    ) -> dict:
        """Files a correction letter (CC-e) against an issued NF-e.

        Only an NF-e has one, so the access key must be an NF-e access
        key (44 characters; the CNPJ slot may carry letters); an NFS-e is
        cancelled and issued again instead. That is checked here. An NF-e
        key sent with DocumentType.NFSE, or one
        for a document the API does not hold, is still answered by the
        API as an APIError with status 409.
        """
        if not _NFE_ACCESS_KEY.fullmatch(access_key):
            raise ValueError(
                "correct is NFe only. NFSe has no correction letter — "
                "cancel and reissue instead."
            )
        if not 15 <= len(correction) <= 1000:
            raise ValueError("correction must be 15 to 1000 characters")

        payload = {
            "document_type": document_type.value,
            "correction": correction,
        }

        return cast(
            dict,
            self._request("POST", f"/invoices/{access_key}/correction", json=payload),
        )

    def reissue(self, invoice_id: str, *, idempotency_key: str | None = None) -> dict:
        """Retries a previous invoice submission by its local id."""
        return cast(
            dict,
            self._request(
                "POST",
                f"/invoices/{invoice_id}/reissue",
                idempotency_key=idempotency_key,
            ),
        )

    def pdf(
        self,
        access_key: str,
        *,
        document_type: DocumentType,
    ) -> bytes:
        """The authorizer's rendering of an authorized document.

        Returns raw bytes — the only method that does not return a
        parsed object. The XML is the legally valid document; this is a
        convenience, and the authorizer's endpoint for it is unstable,
        so an APIError with status 502 means the authorizer is
        unavailable, not that the invoice is wrong. NFS-e only.
        """
        params = {"document_type": document_type.value}
        response = self._send("GET", f"/invoices/{access_key}/pdf", params=params)
        return response.content

    def received(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict:
        """Documents other companies issued against this one.

        Reads what the API already collected; it does not call the
        authorizer. Collecting runs on a schedule there, because the
        SEFAZ caps how many times a CNPJ may ask per day.
        """
        params = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        return cast(dict, self._request("GET", "/received-invoices", params=params))

    def history(
        self,
        *,
        document_type: DocumentType | None = None,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        order_by: str | None = None,
    ) -> dict:
        """This company's own issuance history, newest first.

        The counterpart of received(): that one lists what was issued
        against the company, this one what the company issued.
        """
        params: dict[str, object] = {}
        if document_type is not None:
            params["document_type"] = document_type.value
        if status is not None:
            params["status"] = status
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if sort_by is not None:
            params["sort_by"] = sort_by
        if order_by is not None:
            params["order_by"] = order_by

        return cast(dict, self._request("GET", "/invoices", params=params))

    def submissions(self, invoice_id: str) -> list:
        """Every attempt made for one invoice, and what came back.

        consult() gives the status; this gives the reason. Takes the
        invoice_id because a rejected document has no access key.
        """
        return cast(list, self._request("GET", f"/invoices/{invoice_id}/submissions"))

    def manifest(
        self,
        access_key: str,
        *,
        manifestation: Manifestation,
        reason: str | None = None,
    ) -> dict:
        """The recipient's formal answer to a received document.

        Only `OPERACAO_NAO_REALIZADA` takes a reason, and it requires
        one. Both are fixed rules, so they are checked here rather than
        spending a round trip to be told.
        """
        needs_reason = manifestation is Manifestation.OPERACAO_NAO_REALIZADA
        if needs_reason and not reason:
            raise ValueError(
                "manifestation 210240 (operação não realizada) requires " "a reason"
            )
        if not needs_reason and reason:
            raise ValueError(
                f"manifestation {manifestation.value} does not take a " "reason"
            )

        payload = {"manifestation": manifestation.value}
        if reason:
            payload["reason"] = reason

        return cast(
            dict,
            self._request(
                "POST",
                f"/received-invoices/{access_key}/manifestation",
                json=payload,
            ),
        )
