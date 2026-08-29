# stackin

Human Python SDK for [stackin-api](../stackin_api) — a handful of business fields, nothing about certificates, XML, XSD, signing or SOAP. The API resolves all of that from the issuer's own configuration, identified by `api_key`.

**One class, `Invoice`** — `issue()`/`consult()`/`cancel()`, nothing else to instantiate. Country-specific data plugs into a single `extra` slot instead of growing new parameters per country: `Product` (item data — NCM/CFOP/unit/quantity) for Brazil's NFE. It isn't literally "the document" — that's why the slot is called `extra`, not `document`. Adding a country means adding a type that slot accepts, not touching `Invoice.issue()`'s signature.

## Usage

Get `api_key` from `POST /api/v1/companies` (or `POST /api/v1/companies/{id}/api-key/rotate`) on stackin-api — one key per issuing company, shown once at creation. stackin-api resolves the issuer (CNPJ, state, address, certificate, environment) entirely from it; nothing about the issuer is ever passed on a call.

```python
from stackin import Invoice, DocumentType, Address
from stackin.br import Product  # Brazil-specific — NCM/CFOP

client = Invoice(base_url="https://stackin-api.example.com", api_key="COMPANY_API_KEY")

invoice = client.issue(
    document_type=DocumentType.NFSE,
    client_name="John Doe",
    tax_id="00000000000",
    description="Software development",
    amount=5000.00,
)

status = client.consult("ACCESS_KEY...", document_type=DocumentType.NFSE)
client.cancel(
    "ACCESS_KEY...",
    document_type=DocumentType.NFSE,
    reason="Typo",
)

# NFE requires a Product in the extra slot (NCM/CFOP — Brazil-specific, NFSE has none of this),
# and optionally recipient_address.state to get idDest right on interstate sales:
client.issue(
    document_type=DocumentType.NFE,
    client_name="Buyer Company Ltd",
    tax_id="11111111111111",
    description="Test product",
    amount=100.00,
    extra=Product(ncm="84713012", cfop="5102"),
    recipient_address=Address(state="RJ"),
)
```

`recipient_address` is an `Address`, but despite the name only `.state` is read — the rest of the fields aren't sent anywhere yet. It's the actual customer's state, used only to set `idDest` (interstate vs internal) on NFE — optional, omitting it always produces `idDest=1` (internal).

`extra` accepts `Product` (`stackin.br`) for NFE — required, with `ncm`/`cfop` set — and is ignored for NFSE (a service isn't a physical good, no NCM/CFOP).

## Errors

- `stackin.APIError` — the API responded with a non-2xx status (`status_code`, `detail`) — a 401 here means `api_key` is missing, wrong, or was rotated.
- `stackin.ConnectionFailedError` — the API didn't respond (network/DNS/timeout).
- `ValueError` — `issue()`'s `extra` is set to the wrong type/incomplete for NFE.

## Structure

```
stackin/
├── __init__.py              # Invoice, DocumentType, Address, exceptions
├── br/__init__.py           # public: from stackin.br import Product
└── core/
    ├── client.py             # Invoice class — issue/consult/cancel
    ├── address.py             # Address (pydantic)
    ├── br/product.py          # Product (pydantic) — Brazil/NFE only
    ├── exceptions.py
    └── types.py                # DocumentType
```

Building the full fiscal document (issuer data, service code, tax groups, schema-accurate XML) is [stackin-api](../stackin_api)'s job — configured once per company via `POST /companies`, not passed on every call.
