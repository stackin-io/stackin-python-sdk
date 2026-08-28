"""Client module"""

from __future__ import annotations

import requests

from invoice.core.address import Address
from invoice.core.br.product import Product
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
                items=[
                    Product(description="Widget", amount=50.00, ncm="84713012", cfop="5102"),
                    Product(description="Gadget", amount=30.00, ncm="84713012", cfop="5102"),
                ],
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
        api_key (str | None): The issuing company's API key (from
            `POST /api/v1/companies`), sent as
            `Authorization: Bearer <api_key>` — required, invoice-api
            resolves the issuer entirely from it.
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
        items: list[Product],
        recipient_address: Address | None = None,
    ) -> dict:
        """
        Issues a fiscal document. `POST /api/v1/invoices`.

        `items` is always a list, one entry even for a single product/
        service — each `Product` (`invoice.br`) carries its own
        description/amount plus NCM/CFOP/unit/quantity/... . NFe
        emits one `det` per item; NFSe (a single service) only ever
        uses the first (its description/amount — NFSe has no
        NCM/CFOP).

        The issuer (CNPJ, address, state, certificate, environment)
        isn't a parameter here — invoice-api resolves it entirely
        from `api_key` (the issuing company's own key, set on
        `Invoice(...)`), see `POST /api/v1/companies`.

        Args:
            document_type (DocumentType): NFE or NFSE.
            client_name (str): Customer's name/company name (service
                taker or goods recipient).
            tax_id (str): Customer's CPF/CNPJ, digits only.
            items (list[Product]): One or more line items.
            recipient_address (Address | None): NFE only, optional —
                only `.state` is read, determines `idDest`: internal
                if it matches the issuer's own state (or is unset),
                interstate if it's a different UF, foreign if it's
                the literal `"EX"` (the standard `TUf` value for a
                foreign recipient).

        Returns:
            dict: The authorizer's response (via invoice-api), already
                unwrapped from the API's `{"result": ...}` envelope.

        Raises:
            ValueError: if `items` is empty, or if `document_type` is
                NFE and an item doesn't have `ncm`/`cfop` set.
        """
        if not items:
            raise ValueError("items can't be empty")

        if document_type is DocumentType.NFE:
            for index, item in enumerate(items):
                if not item.ncm:
                    raise ValueError(f"items[{index}].ncm is required for NFE")
                if not item.cfop:
                    raise ValueError(f"items[{index}].cfop is required for NFE")

        payload = {
            "document_type": document_type.value,
            "client_name": client_name,
            "tax_id": tax_id,
            "items": [item.to_dict() for item in items],
        }
        if recipient_address and recipient_address.state:
            payload["recipient_state"] = recipient_address.state

        return self._request("POST", "/invoices", json=payload)

    def consult(
        self,
        access_key: str,
        *,
        document_type: DocumentType,
    ) -> dict:
        """
        Consults a fiscal document by its access key.
        `GET /api/v1/invoices/{access_key}`.

        Args:
            access_key (str): The document's access key.
            document_type (DocumentType): NFE or NFSE.

        Returns:
            dict: The document's current status.
        """
        params = {"document_type": document_type.value}

        return self._request(
            "GET", f"/invoices/{access_key}", params=params
        )

    def cancel(
        self,
        access_key: str,
        *,
        document_type: DocumentType,
        reason: str,
    ) -> dict:
        """
        Cancels a fiscal document by its access key.
        `POST /api/v1/invoices/{access_key}/cancel`.

        Args:
            access_key (str): The document's access key.
            document_type (DocumentType): NFE or NFSE.
            reason (str): Cancellation reason.

        Returns:
            dict: The cancellation result.
        """
        payload = {
            "document_type": document_type.value,
            "reason": reason,
        }

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
