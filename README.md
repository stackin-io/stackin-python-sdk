# invoice

Human Python SDK for [invoice-api](../invoice_api) — a handful of business fields, nothing about certificates, XML, XSD, signing or SOAP. The API resolves all of that from the issuer's own configuration.

**One class, `Invoice`** — `issue()`/`consult()`/`cancel()`, nothing else to instantiate. Country-specific data plugs into a single `extra` slot instead of growing new parameters per country: `Product` (item data — NCM/CFOP/unit/quantity) for Brazil's NFE, `InvoiceDocument` (comprobante metadata — class/point of sale/customer document) for Argentina's WSFEv1. Neither is literally "the document" — that's why the slot is called `extra`, not `document`. Adding a country means adding a type that slot accepts, not touching `Invoice.issue()`'s signature.

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
    issuer_address=Address(city_code="4106902"),   # IBGE code, required for NFSE
)

status = client.consult("ACCESS_KEY...", document_type=DocumentType.NFSE)
client.cancel(
    "ACCESS_KEY...",
    document_type=DocumentType.NFSE,
    reason="Typo",
)

# NFE reads issuer_address.state instead of issuer_address.city_code,
# requires a Product in the extra slot (NCM/CFOP — Brazil-specific, NFSE has none of this),
# and optionally recipient_address.state to get idDest right on interstate sales:
client.issue(
    document_type=DocumentType.NFE,
    client_name="Buyer Company Ltd",
    tax_id="11111111111111",
    description="Test product",
    amount=100.00,
    issuer_address=Address(state="SP"),
    extra=Product(ncm="84713012", cfop="5102"),
    recipient_address=Address(state="RJ"),
)
```

`issuer_address`/`recipient_address` are both `Address`, but despite the name only `.state`/`.city_code` are read — the rest of the fields aren't sent anywhere yet. `issuer_address` picks which authorizer invoice-api calls (the issuer's own UF/city, not a real address — the issuer's full address comes from invoice-api's own config); `recipient_address` is the actual customer's state, used only to set `idDest` (interstate vs internal) on NFE. Neither requires more than the one field `document_type` actually needs.

`extra` accepts `Product` (`invoice.br`) for NFE — required, with `ncm`/`cfop` set — and is ignored for NFSE (a service isn't a physical good, no NCM/CFOP). `invoice.ar.InvoiceDocument` fits the same slot for `DocumentType.FACTURA` (Argentina) — wired end to end through invoice-api, but always returns a 400 today: `app/providers/ar/wsfe/` (WSAA/WSFEv1) has no confirmed host, see `invoice-api/plan/ARGENTINA.md`.

## Errors

- `invoice.APIError` — the API responded with a non-2xx status (`status_code`, `detail`).
- `invoice.ConnectionFailedError` — the API didn't respond (network/DNS/timeout).
- `ValueError` — `issue()` is missing a field its `document_type` needs (`issuer_address.state`/`.city_code`, or `extra` set to the wrong type/incomplete for NFE/FACTURA).

## Structure

```
invoice/
├── __init__.py              # Invoice, DocumentType, Address, exceptions
├── br/__init__.py           # public: from invoice.br import Product
├── ar/__init__.py           # public: from invoice.ar import InvoiceDocument, InvoiceClass
└── core/
    ├── client.py                # Invoice class — issue/consult/cancel
    ├── address.py               # Address (pydantic)
    ├── br/product.py            # Product (pydantic) — Brazil/NFE only
    ├── ar/invoice_document.py   # InvoiceDocument (pydantic) — Argentina/WSFEv1
    ├── exceptions.py
    └── types.py                 # DocumentType
```

Building the full fiscal document (issuer data, service code, tax groups, schema-accurate XML) is [invoice-api](../invoice_api)'s job — configured once with the issuing company's data (CNPJ, state registration, tax regime, certificate), not passed on every call.
