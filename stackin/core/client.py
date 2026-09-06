"""Client module"""

from __future__ import annotations

import os

import requests

from stackin.br.product import Product
from stackin.core.address import Address
from stackin.core.exceptions import APIError, ConnectionFailedError
from stackin.core.types import DocumentType, Environment, Manifestation

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


_NFE_ADDRESS_FIELDS = (
    "street",
    "number",
    "neighborhood",
    "city",
    "state",
    "zip_code",
    "city_code",
)


def _validate_nfe_address(address: Address | None) -> None:
    """NFE needs the full address — a partial one the SEFAZ rejects."""
    if address is None:
        raise ValueError("recipient_address is required for NFE")

    missing = [
        field for field in _NFE_ADDRESS_FIELDS if not getattr(address, field)
    ]
    if missing:
        raise ValueError(
            "recipient_address is missing required fields for NFE: "
            + ", ".join(missing)
        )


class Invoice:
    """Client for issuing, consulting, and cancelling fiscal documents."""

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

    def issue(
        self,
        *,
        document_type: DocumentType,
        client_name: str,
        tax_id: str,
        items: list[Product],
        recipient_address: Address | None = None,
        series: str | None = None,
        number: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        """Issues a fiscal document."""
        if not items:
            raise ValueError("items can't be empty")

        if document_type is DocumentType.NFE:
            for index, item in enumerate(items):
                if not item.ncm:
                    raise ValueError(f"items[{index}].ncm is required for NFE")
                if not item.cfop:
                    raise ValueError(
                        f"items[{index}].cfop is required for NFE"
                    )
            _validate_nfe_address(recipient_address)

        payload = {
            "document_type": document_type.value,
            "client_name": client_name,
            "tax_id": tax_id,
            "items": [item.to_dict() for item in items],
        }
        if recipient_address:
            payload["recipient_address"] = recipient_address.to_dict()
        if series:
            payload["series"] = series
        if number:
            payload["number"] = number

        return self._request(
            "POST",
            "/invoices",
            json=payload,
            idempotency_key=idempotency_key,
        )

    def consult(
        self,
        access_key: str,
        *,
        document_type: DocumentType,
    ) -> dict:
        """Consults a fiscal document by its access key."""
        params = {"document_type": document_type.value}

        return self._request("GET", f"/invoices/{access_key}", params=params)

    def cancel(
        self,
        access_key: str,
        *,
        document_type: DocumentType,
        reason: str,
    ) -> dict:
        """Cancels a fiscal document by its access key."""
        payload = {
            "document_type": document_type.value,
            "reason": reason,
        }

        return self._request(
            "POST", f"/invoices/{access_key}/cancel", json=payload
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

        return self._request("POST", "/invoices/invalidations", json=payload)

    def correct(
        self,
        access_key: str,
        *,
        document_type: DocumentType,
        correction: str,
    ) -> dict:
        """Files a correction letter (CC-e) against an issued document."""
        if not 15 <= len(correction) <= 1000:
            raise ValueError("correction must be 15 to 1000 characters")

        payload = {
            "document_type": document_type.value,
            "correction": correction,
        }

        return self._request(
            "POST", f"/invoices/{access_key}/correction", json=payload
        )

    def reissue(
        self, invoice_id: str, *, idempotency_key: str | None = None
    ) -> dict:
        """Retries a previous invoice submission by its local id."""
        return self._request(
            "POST",
            f"/invoices/{invoice_id}/reissue",
            idempotency_key=idempotency_key,
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
        response = self._send(
            "GET", f"/invoices/{access_key}/pdf", params=params
        )
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

        return self._request("GET", "/received-invoices", params=params)

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

        return self._request("GET", "/invoices", params=params)

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
                "manifestation 210240 (operação não realizada) requires "
                "a reason"
            )
        if not needs_reason and reason:
            raise ValueError(
                f"manifestation {manifestation.value} does not take a "
                "reason"
            )

        payload = {"manifestation": manifestation.value}
        if reason:
            payload["reason"] = reason

        return self._request(
            "POST",
            f"/received-invoices/{access_key}/manifestation",
            json=payload,
        )

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
    ) -> dict:
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
        return body.get("result", body)

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
