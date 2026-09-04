<div align="center">

<img src="https://raw.githubusercontent.com/stackin-io/stackin-python-sdk/master/docs/assets/stackin.png" width="120" />

**Integrate once. Issue everywhere.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](pyproject.toml)
[![PyPI](https://img.shields.io/pypi/v/stackin-python-sdk?style=flat-square)](https://pypi.org/project/stackin-python-sdk/)
[![License](https://img.shields.io/badge/license-MIT-informational?style=flat-square)](https://github.com/stackin-io/stackin-python-sdk)

[API Reference](https://docs.stackin.io) · [Python SDK guide](https://docs.stackin.io/blog/python-sdk)

</div>

---

# stackin

Python SDK for fiscal document issuance — a handful of business fields, nothing about certificates, XML, XSD, signing or SOAP. The API resolves all of that from the issuer's own configuration, identified by `api_key`.

**One class, `Invoice`** — `issue()`/`consult()`/`cancel()`/`reissue()`, nothing else to instantiate. Each line item is a `Product` (`stackin.br`) — `description`/`amount` are universal, everything else (`ncm`/`cfop`/`cest`/tax groups...) is Brazil-specific and only required for NFE; NFSE ignores it.

## Install

```bash
pip install stackin-python-sdk
```

## Usage

Get an `api_key` from the [stackin dashboard](https://app.stackin.io) — select the issuing company, then Settings → API key (context `sdk`). One key per issuing company, shown once at creation. The API resolves the issuer (CNPJ, state, address, certificate, environment) entirely from it; nothing about the issuer is ever passed on a call.

```python
from stackin import Invoice, DocumentType, Address
from stackin.br import Product  # Brazil-specific line item — NCM/CFOP

client = Invoice(api_key="COMPANY_API_KEY")  # defaults to https://sdk.stackin.io

invoice = client.issue(
    document_type=DocumentType.NFSE,
    client_name="John Doe",
    tax_id="00000000000",
    items=[Product(description="Software development", amount=5000.00)],
)

status = client.consult("ACCESS_KEY...", document_type=DocumentType.NFSE)
client.cancel(
    "ACCESS_KEY...",
    document_type=DocumentType.NFSE,
    reason="Typo",
)
client.reissue(invoice["id"])  # retries a rejected/failed submission

# NFE requires ncm/cfop on every item, plus the buyer's full recipient_address:
client.issue(
    document_type=DocumentType.NFE,
    client_name="Buyer Company Ltd",
    tax_id="11111111111111",
    items=[Product(description="Test product", amount=100.00, ncm="84713012", cfop="5102")],
    recipient_address=Address(
        street="Avenida Atlantica",
        number="500",
        neighborhood="Copacabana",
        city="Rio de Janeiro",
        state="RJ",
        zip_code="22010000",
        city_code="3304557",
    ),
)
```

`recipient_address` is an `Address` — the buyer's address, **required for NFE** and ignored for NFSE. Every field is required, `city_code` (the 7-digit IBGE municipality code) included: it becomes `enderDest` on the wire and the SEFAZ rejects a partial one. `state` is also what resolves `idDest` — a buyer in another state is emitted as an interstate operation automatically. A missing or incomplete address raises a `ValueError` locally, before the request goes out.

`items` is a list of `Product` (`stackin.br`) — `description`/`amount` apply to any document type; `ncm`/`cfop` (plus everything else on `Product`: `cest`, tax groups, presumed credits...) are Brazil-specific and required per item for NFE, ignored for NFSE (a service isn't a physical good).

## Errors

- `stackin.APIError` — the API responded with a non-2xx status (`status_code`, `detail`) — a 401 here means `api_key` is missing, wrong, or was rotated.
- `stackin.ConnectionFailedError` — the API didn't respond (network/DNS/timeout).
- `ValueError` — `issue()`'s `items` is empty, missing `ncm`/`cfop` on an item for NFE, or a missing/incomplete `recipient_address` on NFE.

Building the full fiscal document (issuer data, service code, tax groups, schema-accurate XML) is the API's job — configured once per company, not passed on every call.

## Examples

Runnable end-to-end scripts in [`examples/nfe/`](examples/nfe/) and [`examples/nfse/`](examples/nfse/) — one file per field/variant, from the bare minimum to every field filled. `examples/consult_invoice.py`, `examples/cancel_invoice.py`, and `examples/reissue_invoice.py` cover the operations that act on an already-issued document.
