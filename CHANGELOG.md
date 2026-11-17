# Changelog

## v0.17.0 — 2026-11-17

### Features
- **br:** add reduction_ibs and reduction_cbs to IbsCbs (stackin-io/stackin-api#326)

## v0.16.0 — 2026-11-16

### Features
- **client:** company selection, companies() and typed company refusals (#36)

### Docs
- **readme:** document company selection and its errors (#36)

### Tests
- **client:** company header, companies() and the three refusals (#36)

## v0.15.1 — 2026-11-16

### Style
- **address:** ruff format (#33)

## v0.15.0 — 2026-11-16

### Features
- **address:** state_registration for the recipient's IE (#33)

### Tests
- **address:** state_registration masks, ISENTO and refusal (#33)

## v0.14.0 — 2026-11-15

### Features
- **client:** discount, issued_at, purpose, direction, referenced_keys and a buyer abroad on issue()
- **product:** typed fuel group (comb) on br.Product

### Docs
- **readme:** document the API v0.8-v0.9 issue() fields

## v0.13.0 — 2026-11-15

### Features
- **product:** validate the RECOPI check digits

## v0.12.0 — 2026-11-15

### Features
- **client:** external_reference on issue, city_code optional

### Docs
- external_reference and the optional city_code

## v0.11.0 — 2026-11-15

### Features
- **client:** require recipient_address for retained ISS on NFS-e
- **product:** validate the GTIN check digit on barcode
- **client:** reject non-latin1 characters on NF-e
- **product:** validate barcode, xProd and address lengths per XSD 4.00
- **client:** require a 44-digit NF-e key on correct()

### Bug Fixes
- **client:** refuse only what the API refuses in NF-e text
- **client:** accept an alphanumeric CNPJ in the correct() access key
- **client:** require a complete address for retained ISS on NFS-e
- **examples:** pass amount to PresumedCredit
- **client:** type the invoice responses for mypy
- **product:** accept only 8-digit NCM or 00

### Docs
- **client:** say which correct() keys fail locally and which get a 409

### Build
- add mypy and types-requests to the code-quality group

### Style
- apply ruff format to the tree

### Chores
- **platform:** install action-platform

# Changelog — invoice (SDK)

## 0.1.2

### Changed
- `examples/` split into `examples/nfe/` and `examples/nfse/`, one script per field variant instead of two large catalog scripts.
- Multi-line docstrings collapsed to a single line across `stackin/core`.

### Fixed
- `examples/nfse/with_tax_retained.py`/`full.py` now pass a `recipient_address` — required by the API when `tax_retained=True`.

### Added
- Full `unittest.TestCase` coverage for `stackin.core.client`, `stackin.br.product`, `stackin.br.tax`, `stackin.core.address`, `stackin.core.exceptions`, `stackin.core.types` (100%).

## 0.7.0

### Added
- `issue()`'s `recipient_address: Address | None` — sets NFe's `idDest` (interstate vs internal) correctly. Without it, idDest was always 1, wrong for interstate sales.

### Changed (breaking)
- `issue()`'s `address` param renamed to `issuer_address` — same `Address` type, but the old name implied it was the recipient's address when it's actually used to pick the issuer's own authorizer (UF/city). `recipient_address` is the actual customer's state now.

## 0.6.0

### Added
- `DocumentType.FACTURA` — Argentina/WSFEv1, wired through `issue()` end to end. Always fails against invoice-api today (`app/providers/ar/wsfe/` has no confirmed WSAA/WSFEv1 host), but the call reaches the API and gets a real 400, not a client-side dead end.
- `invoice.ar.InvoiceDocument`/`InvoiceClass` — comprobante metadata (class, point of sale, customer document) for FACTURA.

### Changed (breaking)
- `issue()`'s `product` param renamed to `extra: Product | InvoiceDocument | None` — one generic slot for country-specific data instead of a Brazil-named parameter. `Product` still goes there for NFE; `InvoiceDocument` now does too, for FACTURA.

## 0.5.0

### Added
- `Product` (pydantic) — `ncm`/`cfop`/`unit`/`quantity`, required for NFE (`product.ncm`/`product.cfop`), ignored for NFSE. Mirrors `Address`'s pattern instead of loose params on `issue()`.
- `examples/simple_issue_nfse.py` now catches `APIError` too, consistent with the NFE example.

### Changed
- `issue()`/`consult()`/`cancel()` now unwrap invoice-api's `{"result": ...}` envelope — callers get the authorizer's payload directly, not a nested dict.

## Unreleased

### Changed (breaking)
- `issue()`/`consult()`/`cancel()` drop `issuer_address`/`state` params entirely — invoice-api is now multi-tenant and resolves the issuer (CNPJ, state, address, certificate, environment) from `api_key` alone (one key per company, from `POST /api/v1/companies`). `api_key` on `Invoice(...)` goes from optional to required in practice. `recipient_address` is the only `Address` param left on `issue()`.

### Removed
- `DocumentType.FACTURA`, `invoice.ar.InvoiceDocument`/`InvoiceClass` — Argentina scaffold, removed with invoice-api's matching removal (no confirmed WSFEv1 source ever surfaced). `issue()`'s `extra` param is back to `Product | None`. The generic-slot pattern stays: a future country's type just needs to fit `extra` the same way `Product` does.

### Changed (breaking)
- SDK became a thin HTTP client of invoice-api — no longer talks directly to SEFAZ/ADN. All the protocol work (NFe/NFSe, XSD, signing) moved there.
- `Invoice.issue()` now takes a handful of business fields (`client_name`, `tax_id`, `description`, `amount`, `address`) instead of a full technical document (`NFeDoc`/`DPS`).
- `Address` (pydantic) replaces the loose `state`/`municipality_code` params — `address.state` feeds NFE, `address.city_code` feeds NFSE; everything else is optional.
- All field names in English (`client_name`, `tax_id`, `reason`...).

### Removed
- `nfe`/`nfse` (full SOAP/REST clients), `schemas/nfse_servico.py`, `nfse_valores.py`, `nfse_pessoa.py`, `nfe_pessoa.py` (schemas fully matching the official XSD) — all moved to `invoice-api/app/providers/`.
- Client-side certificate/`Config` dependency.

### Added
- `InvalidDocumentError` → later removed again along with the schema validation (no longer applicable, no technical document in the SDK anymore).
- `ConnectionFailedError` now handled correctly even when the API responds with a non-JSON error body (used to blow up with a raw `JSONDecodeError`).
