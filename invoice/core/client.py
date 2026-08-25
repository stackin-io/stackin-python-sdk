"""Client module"""

from __future__ import annotations

import requests

from invoice.core.address import Address
from invoice.core.exceptions import APIError, ConnectionFailedError
from invoice.core.types import DocumentType


class Invoice:
    """
    Import:
        You can import the **Invoice** class directly from invoice:

            from invoice import Invoice, DocumentType

    Example:
        `class` invoice.core.client.Invoice

            client = Invoice(base_url="https://invoice-api.example.com")

            invoice = client.issue(
                document_type=DocumentType.NFE,
                client_name="John Doe",
                tax_id="00000000000",
                description="Test product",
                amount=100.00,
                address=Address(state="PR"),
            )

            status = client.consult(
                "ACCESS_KEY...", document_type=DocumentType.NFSE
            )
            client.cancel(
                "ACCESS_KEY...",
                document_type=DocumentType.NFSE,
                reason="Typo",
            )

    Human SDK — a handful of business fields, nothing about XML, XSD,
    certificates or SOAP. Everything else (issuer data, service code,
    tax groups, schema-accurate XML) is resolved by `invoice-api`
    from the issuer's own configuration — see `invoice-api/README.md`.

    Args:
        base_url (str): Base URL of invoice-api (e.g.
            "https://invoice-api.example.com", without `/api/v1`).
        api_key (str | None): Auth token, if the API requires one
            (sent as `Authorization: Bearer <api_key>`).
        timeout (int): Timeout in seconds for HTTP calls.

    Attributes:
        base_url (str):
        api_key (str | None):
        timeout (int):
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: int = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def issue(
        self,
        *,
        document_type: DocumentType,
        client_name: str,
        tax_id: str,
        description: str,
        amount: float,
        address: Address,
    ) -> dict:
        """
        Issues a fiscal document. `POST /api/v1/invoices`.

        Args:
            document_type (DocumentType): NFE or NFSE.
            client_name (str): Customer's name/company name (service
                taker or goods recipient).
            tax_id (str): Customer's CPF/CNPJ, digits only.
            description (str): Service/product description.
            amount (float): Total amount.
            address (Address): Customer's address — `address.state`
                is required for NFE, `address.city_code` for NFSE
                (no separate `state`/`city_code` args).

        Returns:
            dict: The authorizer's response (via invoice-api), already
                unwrapped from the API's `{"result": ...}` envelope.

        Raises:
            ValueError: if the field `document_type` needs from
                `address` (`state` for NFE, `city_code` for NFSE)
                wasn't set.
        """
        payload = {
            "document_type": document_type.value,
            "client_name": client_name,
            "tax_id": tax_id,
            "description": description,
            "amount": amount,
            "address": address.to_dict(),
        }
        payload.update(self._required_field(document_type, address))

        return self._request("POST", "/invoices", json=payload)

    @staticmethod
    def _required_field(document_type: DocumentType, address: Address) -> dict:
        """`state` (NFE) or `city_code` (NFSE) — whichever
        `document_type` needs, read from `address`."""
        if document_type is DocumentType.NFE:
            if not address.state:
                raise ValueError("address.state is required for NFE")
            return {"state": address.state}

        if not address.city_code:
            raise ValueError("address.city_code is required for NFSE")
        return {"city_code": address.city_code}

    def consult(
        self,
        access_key: str,
        *,
        document_type: DocumentType,
        state: str | None = None,
    ) -> dict:
        """
        Consults a fiscal document by its access key.
        `GET /api/v1/invoices/{access_key}`.

        Args:
            access_key (str): The document's access key.
            document_type (DocumentType): NFE or NFSE.
            state (str | None): Two-letter state code — required
                for NFE.

        Returns:
            dict: The document's current status.
        """
        params = {"document_type": document_type.value}
        if state:
            params["state"] = state

        return self._request(
            "GET", f"/invoices/{access_key}", params=params
        )

    def cancel(
        self,
        access_key: str,
        *,
        document_type: DocumentType,
        reason: str,
        state: str | None = None,
    ) -> dict:
        """
        Cancels a fiscal document by its access key.
        `POST /api/v1/invoices/{access_key}/cancel`.

        Args:
            access_key (str): The document's access key.
            document_type (DocumentType): NFE or NFSE.
            reason (str): Cancellation reason.
            state (str | None): Two-letter state code — required
                for NFE.

        Returns:
            dict: The cancellation result.
        """
        payload = {
            "document_type": document_type.value,
            "reason": reason,
        }
        if state:
            payload["state"] = state

        return self._request(
            "POST", f"/invoices/{access_key}/cancel", json=payload
        )

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
