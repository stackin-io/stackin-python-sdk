# invoice

Human Python SDK for [invoice-api](../invoice_api) — a handful of business fields, nothing about certificates, XML, XSD, signing or SOAP. The API resolves all of that from the issuer's own configuration.

## Usage

```python
from invoice import Invoice, DocumentType, Address

client = Invoice(base_url="https://invoice-api.example.com")

invoice = client.issue(
    document_type=DocumentType.NFSE,
    client_name="John Doe",
    tax_id="00000000000",
    description="Software development",
    amount=5000.00,
    address=Address(city_code="4106902"),   # IBGE code, required for NFSE
)

status = client.consult("ACCESS_KEY...", document_type=DocumentType.NFSE)
client.cancel(
    "ACCESS_KEY...",
    document_type=DocumentType.NFSE,
    reason="Typo",
)

# NFE reads state from address.state instead of address.city_code:
client.issue(
    document_type=DocumentType.NFE,
    client_name="Buyer Company Ltd",
    tax_id="11111111111111",
    description="Test product",
    amount=100.00,
    address=Address(state="SP"),
)
```

`Address` only requires the field `document_type` actually needs (`state` for NFE, `city_code` for NFSE) — everything else (`street`, `number`, `neighborhood`, `city`, `zip_code`) is optional, fill in only what you have.

## Errors

- `invoice.APIError` — the API responded with a non-2xx status (`status_code`, `detail`).
- `invoice.ConnectionFailedError` — the API didn't respond (network/DNS/timeout).
- `ValueError` — `issue()` is missing the address field its `document_type` needs.

## Structure

```
invoice/
├── __init__.py
└── core/
    ├── client.py       # Invoice class — issue/consult/cancel
    ├── address.py       # Address (pydantic)
    ├── exceptions.py
    └── types.py        # DocumentType
```

Building the full fiscal document (issuer data, service code, tax groups, schema-accurate XML) is [invoice-api](../invoice_api)'s job — configured once with the issuing company's data (CNPJ, state registration, tax regime, certificate), not passed on every call.
