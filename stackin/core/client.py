"""Client module"""

from __future__ import annotations

import os
import re
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Literal, cast

import requests

from stackin.br.export import Export
from stackin.br.product import Product
from stackin.core.address import Address
from stackin.core.exceptions import ConnectionFailedError, _api_error
from stackin.core.types import (
    Direction,
    DocumentType,
    Environment,
    Manifestation,
    Purpose,
)
from stackin.core.usage import ReceivedSync, Usage

DEFAULT_BASE_URL = "https://sdk.stackin.io"

COMPANY_HEADER = "X-Stackin-Company"

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


def _page_params(
    limit: int | None,
    offset: int | None,
    sort_by: str | None,
    order_by: str | None,
) -> dict[str, Any]:
    """The API's pagination query, leaving out what was not passed."""
    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if sort_by is not None:
        params["sort_by"] = sort_by
    if order_by is not None:
        params["order_by"] = order_by
    return params


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
        company: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """`company` is the UUID or CNPJ every request names in the
        X-Stackin-Company header, for a credential that covers several
        companies. Left unset, no header is sent.

        `headers` are sent on every request, for a caller that has to
        identify itself to the API (an integration name, a tool). They
        never replace the SDK's own: Authorization, Idempotency-Key and
        X-Stackin-Company always win."""
        resolved_url = _resolve_base_url(base_url, environment)
        self.base_url = resolved_url.rstrip("/")
        self.api_key = api_key or os.environ.get("STACKIN_API_KEY")
        self.timeout = timeout
        self.company = company
        self.extra_headers = dict(headers or {})

    def _headers(
        self,
        idempotency_key: str | None = None,
        company: str | None = None,
    ) -> dict:
        headers = dict(self.extra_headers)
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        if selected := company or self.company:
            headers[COMPANY_HEADER] = selected
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        idempotency_key: str | None = None,
        company: str | None = None,
    ) -> Any:
        response = self._send(
            method,
            path,
            json=json,
            params=params,
            idempotency_key=idempotency_key,
            company=company,
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
        company: str | None = None,
    ) -> requests.Response:
        url = f"{self.base_url}/api/v1{path}"

        try:
            response = requests.request(
                method,
                url,
                json=json,
                params=params,
                headers=self._headers(idempotency_key, company),
                timeout=self.timeout,
            )
        except requests.RequestException as error:
            raise ConnectionFailedError(str(error)) from error

        if not response.ok:
            try:
                body = response.json() if response.content else {}
            except ValueError:
                body = {}
            detail = (
                body.get("detail", response.text)
                if isinstance(body, dict)
                else response.text
            )
            raise _api_error(
                response.status_code,
                detail,
                body,
                response.headers,
            )

        return response


class Invoice(_Client):
    """Client for issuing, consulting, and cancelling fiscal documents.

    Every method but companies() also takes `company`, which names the
    company for that one call over the client's own.
    """

    def issue(
        self,
        *,
        document_type: DocumentType,
        client_name: str | None = None,
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
        company: str | None = None,
        client_id: str | None = None,
        update_client: bool = False,
        client_email: str | None = None,
        client_phone: str | None = None,
        contingency: bool = False,
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

        `client_id` names a saved client (see Clients): its name,
        tax_id, foreign_id and address fill whichever of client_name,
        tax_id, foreign_id and recipient_address are left out, and the
        ones passed win. Those four are then no longer required here;
        the API checks the merged request. After a successful issuance
        a new recipient is saved as a client; `update_client=True`
        rewrites an existing one with this request's recipient data.

        `client_email` and `client_phone` are the recipient's contact,
        saved on the Stackin client after a successful issuance (on an
        existing client only with `update_client=True`, and only the ones
        sent: a missing one never erases a saved one). They are not
        written into the fiscal document, and a reissue does not touch
        the client. Each is left out of the body when unset; the API
        owns the format rules (a valid e-mail; 8 to 15 digits for the
        phone, optional leading +) and answers a bad one as an APIError.

        A line with `item_id` names a catalog item (see Items): it fills
        whichever of the line's description, price, unit, barcode, ncm,
        cfop, cest, tax and service fields are left out, and the ones the
        line sends win. Its `description` is then optional, and the NF-e
        ncm and cfop are left to the API, which checks the filled line.

        `contingency=True` sends an NF-e through the UF's contingency
        authorizer (SVC-AN/SVC-RS, tpEmis 6/7) for when its own is down.
        Left False, it is not sent.
        """
        if not items:
            raise ValueError("items can't be empty")

        from_client = client_id is not None
        if client_name is None and not from_client:
            raise ValueError("client_name is required unless client_id is given")

        abroad = document_type is DocumentType.NFE and _is_abroad(recipient_address)
        if tax_id is None and not abroad and not from_client:
            raise ValueError(
                "tax_id is required, except on an NF-e to a buyer abroad "
                "(recipient_address.state EX)"
            )

        if document_type is DocumentType.NFE:
            for index, item in enumerate(items):
                if (
                    item.description is not None
                    and len(item.description) > _NFE_DESCRIPTION_MAX
                ):
                    raise ValueError(
                        f"items[{index}].description exceeds "
                        f"{_NFE_DESCRIPTION_MAX} characters (NF-e xProd limit)"
                    )
                if item.item_id is not None:
                    continue
                if not item.ncm:
                    raise ValueError(f"items[{index}].ncm is required for NFE")
                if not item.cfop:
                    raise ValueError(f"items[{index}].cfop is required for NFE")
            if recipient_address is not None or not from_client:
                _validate_nfe_address(recipient_address)
        retained = any(item.tax_retained for item in items)
        if document_type is DocumentType.NFSE and retained:
            if recipient_address is not None or not from_client:
                _validate_nfse_retained_address(recipient_address)

        payload: dict[str, Any] = {"document_type": document_type.value}
        if client_id is not None:
            payload["client_id"] = client_id
        if client_name is not None:
            payload["client_name"] = client_name
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
        if update_client:
            payload["update_client"] = True
        if client_email is not None:
            payload["client_email"] = client_email
        if client_phone is not None:
            payload["client_phone"] = client_phone
        if contingency:
            payload["contingency"] = True

        return cast(
            dict,
            self._request(
                "POST",
                "/invoices",
                json=payload,
                idempotency_key=idempotency_key,
                company=company,
            ),
        )

    def consult(
        self,
        access_key: str,
        *,
        document_type: DocumentType,
        company: str | None = None,
    ) -> dict:
        """Consults a fiscal document by its access key."""
        params = {"document_type": document_type.value}

        return cast(
            dict,
            self._request(
                "GET",
                f"/invoices/{access_key}",
                params=params,
                company=company,
            ),
        )

    def cancel(
        self,
        access_key: str,
        *,
        document_type: DocumentType,
        reason: str,
        idempotency_key: str | None = None,
        company: str | None = None,
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
                company=company,
            ),
        )

    def invalidate(
        self,
        *,
        series: str,
        number_start: int,
        number_end: int,
        reason: str,
        company: str | None = None,
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
            dict,
            self._request(
                "POST",
                "/invoices/invalidations",
                json=payload,
                company=company,
            ),
        )

    def invalidations(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        order_by: str | None = None,
        company: str | None = None,
    ) -> dict:
        """The numbering ranges this company already invalidated, a page.

        Each row carries the range, the reason, the SEFAZ `status` and its
        `protocol`. Read it before invalidate() to avoid reporting the
        same range twice.
        """
        return cast(
            dict,
            self._request(
                "GET",
                "/invoices/invalidations",
                params=_page_params(limit, offset, sort_by, order_by),
                company=company,
            ),
        )

    def correct(
        self,
        access_key: str,
        *,
        document_type: DocumentType,
        correction: str,
        company: str | None = None,
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
            self._request(
                "POST",
                f"/invoices/{access_key}/correction",
                json=payload,
                company=company,
            ),
        )

    def reissue(
        self,
        invoice_id: str,
        *,
        idempotency_key: str | None = None,
        company: str | None = None,
    ) -> dict:
        """Retries a previous invoice submission by its local id."""
        return cast(
            dict,
            self._request(
                "POST",
                f"/invoices/{invoice_id}/reissue",
                idempotency_key=idempotency_key,
                company=company,
            ),
        )

    def pdf(
        self,
        access_key: str,
        *,
        document_type: DocumentType,
        company: str | None = None,
    ) -> bytes:
        """The printable rendering of an authorized document, as a PDF.

        The API draws it itself from the authorized XML: the DANFE for
        an NF-e, the DANFSe for an NFS-e. Returns raw bytes, the only
        method that does not return a parsed object. The XML stays the
        legally valid document; the PDF is its representation.
        """
        params = {"document_type": document_type.value}
        response = self._send(
            "GET",
            f"/invoices/{access_key}/pdf",
            params=params,
            company=company,
        )
        return response.content

    def received(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        company: str | None = None,
    ) -> dict:
        """Documents other companies issued against this one.

        Reads what the API already collected; it does not call the
        SEFAZ. Collecting runs on a schedule there, every six hours, and
        sync_received() asks for what is new right away. After a read
        that finds nothing more, the SEFAZ makes the CNPJ wait an hour.

        The first 50 received a month are included in every plan; each
        one after that takes R$ 0,05 from the account credit, unless
        usage().received_free exempts the account.
        """
        params = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        return cast(
            dict,
            self._request("GET", "/received-invoices", params=params, company=company),
        )

    def sync_received(self, *, company: str | None = None) -> ReceivedSync:
        """Asks the SEFAZ now for documents issued against the company.

        Resumes where the last read stopped and stores what arrives; read
        it with received(). Within the SEFAZ's one-hour wait after a read
        that found nothing more, raises RateLimitedError with code
        DISTRIBUTION_COOLDOWN, `retry_at` and `retry_after`.
        """
        result = self._request("POST", "/received-invoices/sync", company=company)
        return ReceivedSync.model_validate(result)

    def usage(self, *, company: str | None = None) -> Usage:
        """The plan behind the company and how much of it is used.

        The numbers are the paying account's, shared by every company it
        holds.
        """
        return Usage.model_validate(
            self._request("GET", "/company/usage", company=company)
        )

    def history(
        self,
        *,
        document_type: DocumentType | None = None,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        order_by: str | None = None,
        external_reference: str | None = None,
        fields: Literal["full", "summary"] | None = None,
        company: str | None = None,
    ) -> dict:
        """This company's own issuance history, newest first.

        The counterpart of received(): that one lists what was issued
        against the company, this one what the company issued.

        `external_reference` keeps only the documents issued with that
        exact reference. `fields="summary"` returns a lighter row per
        document, with `items` and `fiscal_operation` left null; consult
        one document for its lines.
        """
        params: dict[str, object] = {}
        if document_type is not None:
            params["document_type"] = document_type.value
        if status is not None:
            params["status"] = status
        if external_reference is not None:
            params["external_reference"] = external_reference
        if fields is not None:
            params["fields"] = fields
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if sort_by is not None:
            params["sort_by"] = sort_by
        if order_by is not None:
            params["order_by"] = order_by

        return cast(
            dict,
            self._request("GET", "/invoices", params=params, company=company),
        )

    def submissions(self, invoice_id: str, *, company: str | None = None) -> list:
        """Every attempt made for one invoice, and what came back.

        consult() gives the status; this gives the reason. Takes the
        invoice_id because a rejected document has no access key.
        """
        return cast(
            list,
            self._request(
                "GET",
                f"/invoices/{_invoice_segment(invoice_id)}/submissions",
                company=company,
            ),
        )

    def rejection(self, invoice_id: str, *, company: str | None = None) -> dict:
        """Why a rejected document was refused, and what to change.

        submissions() has the authorizer's own answer; this reads it for
        someone who does not speak SEFAZ: `code`, `message`,
        `explanation`, `steps`, the `field` to fix and, when there is
        one, a `suggested` value. Takes the invoice_id, like
        submissions(). A document that is not rejected is an APIError
        409.
        """
        return cast(
            dict,
            self._request(
                "GET",
                f"/invoices/{_invoice_segment(invoice_id)}/rejection",
                company=company,
            ),
        )

    def classify(
        self,
        description: str,
        *,
        document_type: DocumentType,
        recipient_state: str | None = None,
        answers: dict[str, Any] | None = None,
        company: str | None = None,
    ) -> dict:
        """A suggested fiscal classification for one item's description.

        A suggestion, never a decision: `primary_candidate` and
        `alternative_candidates` carry the NCM, CFOP, CST/CSOSN, CEST or
        service code, each read from the published tables, with a
        `confidence`, and `missing_information` lists what would settle
        it (pass those back in `answers`). Someone confirms it before it
        goes on an item; the codes decide the tax owed.
        """
        if not 3 <= len(description) <= 500:
            raise ValueError("description must be 3 to 500 characters")
        if recipient_state is not None and len(recipient_state) != 2:
            raise ValueError("recipient_state must be a two-letter UF")

        payload: dict[str, Any] = {
            "description": description,
            "document_type": DocumentType(document_type).value,
        }
        if recipient_state is not None:
            payload["recipient_state"] = recipient_state.upper()
        if answers:
            payload["answers"] = dict(answers)

        return cast(
            dict,
            self._request("POST", "/ai/classify", json=payload, company=company),
        )

    def stats(self, *, days: int | None = None, company: str | None = None) -> dict:
        """Counts of this company's documents, and the last `days` of them.

        `total`, `by_document_type` and `by_status` cover every document;
        `current_period`/`previous_period` compare the last `days` (1 to
        365, the API's default 30) with the ones before, and
        `daily_series` has one row per day.
        """
        params: dict[str, Any] = {}
        if days is not None:
            if not 1 <= days <= 365:
                raise ValueError("days must be 1 to 365")
            params["days"] = days

        return cast(
            dict,
            self._request("GET", "/invoices/stats", params=params, company=company),
        )

    def readiness(self, *, company: str | None = None) -> dict:
        """Whether the company can issue right now, and if not, why.

        `ready` (at least one document type can be issued) is False with
        `missing` naming the cause: certificate, certificate_expired,
        certificate_unreadable, address, state_registration (NF-e) or
        plan. `by_document_type` breaks it down per nfe/nfse — `ready`,
        `missing` and `warnings`, each issue a `code` plus, for address,
        the `fields` at fault — and `fix_url` is the dashboard screen for
        the first blocker (None when nothing blocks). Also
        `certificate_expires_at`, `tax_regime` (CRT), `state`, the
        `default_series` per document type and `suggested_fiscal_fields`,
        what the CNPJ registry suggests where it differs, never applied.
        Ask before a first document instead of failing it; fix the
        address and fiscal fields with `Company.update()`.
        """
        return cast(dict, self._request("GET", "/company", company=company))

    def manifest(
        self,
        access_key: str,
        *,
        manifestation: Manifestation,
        reason: str | None = None,
        company: str | None = None,
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
                company=company,
            ),
        )

    def companies(self) -> dict:
        """The companies this credential covers, and what it may do in each.

        Returns `{environment, companies: [{company_id, name, tax_id,
        permissions}]}`. Either id of a listed company is what `company`
        takes. An API key lists its one company with every permission.
        """
        return cast(dict, self._request("GET", "/me/companies"))


def _invoice_segment(invoice_id: str) -> str:
    """The invoice id as one escaped path segment (see reference._segment)."""
    from stackin.core.reference import _segment

    return _segment(invoice_id)
