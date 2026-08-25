# Changelog — invoice (SDK)

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
