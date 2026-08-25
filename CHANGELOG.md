# Changelog — invoice (SDK)

## 0.5.0

### Added
- `Product` (pydantic) — `ncm`/`cfop`/`unit`/`quantity`, required for NFE (`product.ncm`/`product.cfop`), ignored for NFSE. Mirrors `Address`'s pattern instead of loose params on `issue()`.
- `examples/simple_issue_nfse.py` now catches `APIError` too, consistent with the NFE example.

### Changed
- `issue()`/`consult()`/`cancel()` now unwrap invoice-api's `{"result": ...}` envelope — callers get the authorizer's payload directly, not a nested dict.

## Unreleased

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
