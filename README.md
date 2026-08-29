<div align="center">

<img src="https://raw.githubusercontent.com/stackin-io/stackin-python-sdk/main/docs/assets/stackin.png" width="120" />

**Human Python SDK for fiscal document issuance. Give it a sale, get back an NFe/NFSe.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-informational?style=flat-square)](https://github.com/stackin-io/stackin-python-sdk)

</div>

---

# stackin

Human Python SDK for fiscal document issuance — a handful of business fields, nothing about certificates, XML, XSD, signing or SOAP. The API resolves all of that from the issuer's own configuration, identified by `api_key`.

**One class, `Invoice`** — `issue()`/`consult()`/`cancel()`, nothing else to instantiate. Country-specific data plugs into a single `extra` slot instead of growing new parameters per country: `Product` (item data — NCM/CFOP/unit/quantity) for Brazil's NFE. It isn't literally "the document" — that's why the slot is called `extra`, not `document`. Adding a country means adding a type that slot accepts, not touching `Invoice.issue()`'s signature.

## Install

```bash
pip install stackin
```

## Usage

Get an `api_key` from the API — one key per issuing company, shown once at creation. The API resolves the issuer (CNPJ, state, address, certificate, environment) entirely from it; nothing about the issuer is ever passed on a call.

```python
from stackin import Invoice, DocumentType, Address
from stackin.br import Product  # Brazil-specific — NCM/CFOP

client = Invoice(base_url="YOUR_API_URL", api_key="COMPANY_API_KEY")

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

Building the full fiscal document (issuer data, service code, tax groups, schema-accurate XML) is the API's job — configured once per company, not passed on every call.

## Examples

Runnable end-to-end scripts in [`examples/`](examples/) — `simple_issue_nfe.py` and `simple_issue_nfse.py`, each with a catalog of realistic line items covering every optional field.

## Commit Style

| Icon | Type      | Description                                |
|------|-----------|--------------------------------------------|
| ⚙️   | FEATURE   | New feature                                |
| 📝   | PEP8      | Formatting fixes following PEP8            |
| 📌   | ISSUE     | Reference to issue                         |
| 🪲   | BUG       | Bug fix                                    |
| 📘   | DOCS      | Documentation changes                      |
| 📦   | PyPI      | PyPI releases                              |
| ❤️️   | TEST      | Automated tests                            |
| ⬆️   | CI/CD     | Changes in continuous integration/delivery |
| ⚠️   | SECURITY  | Security improvements                      |
