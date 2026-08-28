#!/usr/bin/env python
"""Error handling — what the SDK raises and when, without needing a
real server or certificate for most of it.

- ValueError: bad call, caught before any request is made.
- ConnectionFailedError: invoice-api unreachable (network/DNS/timeout).
- APIError: invoice-api reached, but rejected the request (4xx/5xx),
  `.status_code`/`.detail` carry the API's own error.
"""

import os

from dotenv import load_dotenv

from invoice import APIError, ConnectionFailedError, DocumentType, Invoice
from invoice.br import Product

load_dotenv()


def missing_ncm_raises_value_error():
    client = Invoice(base_url="http://localhost:8000", api_key="irrelevant")
    try:
        client.issue(
            document_type=DocumentType.NFE,
            client_name="Comprador Teste",
            tax_id="11222333000181",
            items=[Product(description="Produto sem NCM", amount=100.00)],
        )
    except ValueError as error:
        print("ValueError (expected):", error)


def empty_items_raises_value_error():
    client = Invoice(base_url="http://localhost:8000", api_key="irrelevant")
    try:
        client.issue(
            document_type=DocumentType.NFSE,
            client_name="Comprador Teste",
            tax_id="11222333000181",
            items=[],
        )
    except ValueError as error:
        print("ValueError (expected):", error)


def unreachable_server_raises_connection_failed():
    """Port 9 is the TCP "discard" service — always refuses/closes
    fast, good enough to simulate an unreachable invoice-api."""
    client = Invoice(base_url="http://localhost:9", api_key="irrelevant", timeout=3)
    try:
        client.issue(
            document_type=DocumentType.NFSE,
            client_name="Comprador Teste",
            tax_id="11222333000181",
            items=[Product(description="Servico", amount=100.00)],
        )
    except ConnectionFailedError as error:
        print("ConnectionFailedError (expected):", error)


def wrong_api_key_raises_api_error():
    client = Invoice(
        base_url="http://localhost:8000", api_key="definitely-not-a-real-key"
    )
    try:
        client.issue(
            document_type=DocumentType.NFSE,
            client_name="Comprador Teste",
            tax_id="11222333000181",
            items=[Product(description="Servico", amount=100.00)],
        )
    except ConnectionFailedError:
        print("invoice-api is not running on localhost:8000 — skipping this case")
    except APIError as error:
        print(f"APIError (expected): [{error.status_code}] {error.detail}")


def main():
    missing_ncm_raises_value_error()
    empty_items_raises_value_error()
    unreachable_server_raises_connection_failed()
    wrong_api_key_raises_api_error()


if __name__ == "__main__":
    main()
