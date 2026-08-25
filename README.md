# invoice

Human Python SDK for [invoice-api](../invoice_api) — a handful of business fields, nothing about certificates, XML, XSD, signing or SOAP. The API resolves all of that from the issuer's own configuration.

**One class, `Invoice`** — `issue()`/`consult()`/`cancel()`, nothing else to instantiate. Country-specific data plugs into a single `document` slot instead of growing new parameters per country: `Product` for Brazil's NFE today, `InvoiceDocument` (`invoice.ar`, not wired server-side yet) for Argentina's WSFEv1 tomorrow. Adding a country means adding a type that slot accepts, not touching `Invoice.issue()`'s signature.

## Usage

```python
from invoice import Invoice, DocumentType, Address
from invoice.br import Product  # Brazil-specific — NCM/CFOP

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

# NFE reads state from address.state instead of address.city_code,
# and requires a Product in the document slot (NCM/CFOP — Brazil-specific, NFSE has none of this):
client.issue(
    document_type=DocumentType.NFE,
    client_name="Buyer Company Ltd",
    tax_id="11111111111111",
    description="Test product",
    amount=100.00,
    address=Address(state="SP"),
    document=Product(ncm="84713012", cfop="5102"),
)
```

`Address` only requires the field `document_type` actually needs (`state` for NFE, `city_code` for NFSE) — everything else (`street`, `number`, `neighborhood`, `city`, `zip_code`) is optional, fill in only what you have.

`document` accepts `Product` (`invoice.br`) for NFE — required, with `ncm`/`cfop` set — and is ignored for NFSE (a service isn't a physical good, no NCM/CFOP). `invoice.ar.InvoiceDocument` fits the same slot but isn't usable yet — invoice-api has no Argentina `DocumentType` to send it to.

## Errors

- `invoice.APIError` — the API responded with a non-2xx status (`status_code`, `detail`).
- `invoice.ConnectionFailedError` — the API didn't respond (network/DNS/timeout).
- `ValueError` — `issue()` is missing a field its `document_type` needs (an address field, or a `Product` with `ncm`/`cfop` set, for NFE).

## Structure

```
invoice/
├── __init__.py            # Invoice, DocumentType, Address, exceptions
├── br/__init__.py          # public: from invoice.br import Product
├── ar/__init__.py          # public: from invoice.ar import InvoiceDocument (scaffold)
└── core/
    ├── client.py           # Invoice class — issue/consult/cancel
    ├── address.py          # Address (pydantic)
    ├── br/product.py       # Product (pydantic) — Brazil/NFE only
    ├── ar/invoice_document.py  # InvoiceDocument (pydantic) — Argentina/WSFEv1, scaffold
    ├── exceptions.py
    └── types.py             # DocumentType
```

Building the full fiscal document (issuer data, service code, tax groups, schema-accurate XML) is [invoice-api](../invoice_api)'s job — configured once with the issuing company's data (CNPJ, state registration, tax regime, certificate), not passed on every call.
