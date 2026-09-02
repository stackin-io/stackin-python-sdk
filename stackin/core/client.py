"""Client module"""

from __future__ import annotations

import os

import requests

from stackin.br.product import Product
from stackin.core.address import Address
from stackin.core.exceptions import APIError, ConnectionFailedError
from stackin.core.types import DocumentType, Environment

DEFAULT_BASE_URL = "https://sdk.stackin.io"

_ENVIRONMENT_URLS = {
    Environment.LOCAL: "http://localhost:8000",
    Environment.TEST: DEFAULT_BASE_URL,
    Environment.PRODUCTION: DEFAULT_BASE_URL,
}


def _resolve_base_url(
    base_url: str | None, environment: Environment | str | None
) -> str:
    """Resolution order: explicit param, then env var, then environment's default."""
    if base_url:
        return base_url
    if url := os.environ.get("STACKIN_BASE_URL"):
        return url

    if environment is not None:
        return _ENVIRONMENT_URLS[Environment(environment)]
    if env_name := os.environ.get("STACKIN_ENVIRONMENT"):
        return _ENVIRONMENT_URLS[Environment(env_name)]
    return DEFAULT_BASE_URL


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

        return self._request("POST", "/invoices", json=payload)

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

    def reissue(self, invoice_id: str) -> dict:
        """Retries a previous invoice submission by its local id."""
        return self._request("POST", f"/invoices/{invoice_id}/reissue")

    def _headers(self) -> dict:
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        url = f"{self.base_url}/api/v1{path}"

        try:
            response = requests.request(
                method,
                url,
                json=json,
                params=params,
                headers=self._headers(),
                timeout=self.timeout,
            )
        except requests.RequestException as error:
            raise ConnectionFailedError(str(error)) from error

        try:
            body = response.json() if response.content else {}
        except ValueError:
            body = {}

        if not response.ok:
            raise APIError(
                status_code=response.status_code,
                detail=body.get("detail", response.text),
            )

        return body.get("result", body)
