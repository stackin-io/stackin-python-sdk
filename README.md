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

**One class, `Invoice`** — `issue()`/`consult()`/`cancel()`/`reissue()`/`correct()`/`invalidate()`/`pdf()`/`history()`/`submissions()`/`received()`/`sync_received()`/`manifest()`/`usage()`, nothing else to instantiate. Each line item is a `Product` (`stackin.br`) — `description` plus either `unit_price` or `amount` are universal, everything else (`ncm`/`cfop`/`cest`/tax groups...) is Brazil-specific and only required for NFE; NFSE ignores it.

## What a line item is worth

`unit_price` is the price of **one unit**. `amount` is the **gross total of
the line's products**, before discount, freight, insurance and other
expenses. Send either; sending both asserts that they agree.

```python
from decimal import Decimal

# One unit
Product(description="Consultoria", quantity=Decimal("1"), unit_price=Decimal("1500.00"))

# More than one unit — amount is computed as 2 x 120.00 = 240.00
Product(description="Teclado", quantity=Decimal("2"), unit_price=Decimal("120.00"))

# A fractional quantity — 1.5 x 30.00 = 45.00
Product(description="Cabo", quantity=Decimal("1.5"), unit_price=Decimal("30.00"))

# Legacy: amount alone still means the line's gross total
Product(description="Servico", quantity=Decimal("3"), amount=Decimal("150.00"))

# Both, checked against each other before the document is transmitted
Product(
    description="Teclado",
    quantity=Decimal("2"),
    unit_price=Decimal("120.00"),
    amount=Decimal("240.00"),
)

# With charges: 5000.00 - 100.50 + 40.00 + 10.00 = 4949.50 on the note
Product(
    description="Servidor",
    quantity=Decimal("2"),
    unit_price=Decimal("2500.00"),
    discount=100.50,
    freight=40.00,
    insurance=10.00,
)
```

Amounts that do not add up are refused before the authorizer sees them,
with a `422` naming the line and both numbers:

```json
{
  "detail": {
    "code": "ITEM_TOTAL_MISMATCH",
    "field": "items[0].amount",
    "message": "amount is 50.00, but quantity x unit_price is 150.00.",
    "expected": "150.00",
    "received": "50.00"
  }
}
```

### Migrating

```text
Before:  quantity = 3, amount = 150.00
After:   quantity = 3, unit_price = 50.00
```

Nothing has to migrate. `amount` keeps the meaning it always had and is
not deprecated in this release; a line sent with `amount` alone is built
exactly as it was before.

## Install

```bash
pip install stackin-python-sdk
```

## Usage

Get an `api_key` from the [stackin dashboard](https://app.stackin.io) — select the issuing company, then Settings → API key (context `sdk`). One key per issuing company, shown once at creation. The API resolves the issuer (CNPJ, state, address, certificate, environment) entirely from it; nothing about the issuer is ever passed on a call.

```python
from decimal import Decimal

from stackin import Invoice, DocumentType, Address
from stackin.br import Product  # Brazil-specific line item — NCM/CFOP

client = Invoice(api_key="COMPANY_API_KEY")  # defaults to https://sdk.stackin.io

invoice = client.issue(
    document_type=DocumentType.NFSE,
    client_name="John Doe",
    tax_id="00000000000",
    items=[Product(description="Software development", unit_price=Decimal("5000.00"))],
)

status = client.consult("ACCESS_KEY...", document_type=DocumentType.NFSE)
client.cancel(
    "ACCESS_KEY...",
    document_type=DocumentType.NFSE,
    reason="Typo",
)
client.reissue(invoice["id"])  # retries a rejected/failed submission

# The PDF, as raw bytes: the API draws the DANFE for an NF-e and the
# DANFSe for an NFS-e itself. The XML stays the legally valid document.
with open("nota.pdf", "wb") as file:
    file.write(client.pdf(access_key, document_type=DocumentType.NFSE))

# NFE requires ncm/cfop on every item, plus the buyer's full recipient_address:
client.issue(
    document_type=DocumentType.NFE,
    client_name="Buyer Company Ltd",
    tax_id="11111111111111",
    items=[
        Product(
            description="Teclado",
            quantity=Decimal("2"),
            unit_price=Decimal("120.00"),
            unit="UN",
            ncm="84716052",
            cfop="5102",
        )
    ],
    recipient_address=Address(
        street="Avenida Atlantica",
        number="500",
        neighborhood="Copacabana",
        city="Rio de Janeiro",
        state="RJ",
        zip_code="22010000",
    ),
    external_reference="order-1234",
)
```

`external_reference` is your own id for the document — an order number, a ticket. It is stored as sent, returned on every read and webhook, and `GET /invoices?external_reference=` finds the document by it.

`recipient_address` is an `Address` — the buyer's address, **required for NFE**. On NFE street, number, neighborhood, city, state and zip code are required (a buyer abroad trades the zip code for a country, see [A buyer abroad](#a-buyer-abroad-nf-e)): it becomes `enderDest` on the wire and the SEFAZ rejects a partial one. `city_code` (the 7-digit IBGE municipality code) may be left out — the API resolves it from city and state and answers `CITY_NOT_FOUND` (422) when it cannot; send it yourself when the name is ambiguous. `state` is also what resolves `idDest` — a buyer in another state is emitted as an interstate operation automatically. On NFSE it is the tomador's address: optional, except when any item has `tax_retained=True` (the ISSQN retained by the tomador), where the city authorizer refuses the document without it (`E0237`) — then every field except `city_code` is required. In both cases a missing or incomplete address raises a `ValueError` locally, before the request goes out.

`items` is a list of `Product` (`stackin.br`) — `description`/`amount` apply to any document type; `ncm`/`cfop` (plus everything else on `Product`: `cest`, tax groups, presumed credits...) are Brazil-specific and required per item for NFE, ignored for NFSE (a service isn't a physical good). `ncm` is the full 8 digits, or `00` for a service line — the SEFAZ rejects any other short code (rejection `777`), so one fails at construction. `recopi_number` must be the 20-digit RECOPI number; the SDK checks its two modulo-11 check digits (MOC §8.5) before sending.

## Optional document fields

Each of these is left out of the request body when unset, so a call that does not use them sends exactly what it sent before. The SDK checks only types and enums locally; the fiscal rules on them are the API's, answered as an `APIError` that names the rule.

`discount` — a `Decimal` (zero or more) taken off the whole document; the API spreads it over the lines:

```python
client.issue(..., discount=Decimal("15.00"))
```

`issued_at` — the emission moment, a **timezone-aware** `datetime`, sent as ISO 8601 with its offset. A naive one raises `ValueError`. NF-e: at most 30 days back and 5 minutes ahead; NFS-e: never ahead.

```python
from datetime import datetime, timedelta, timezone

client.issue(..., issued_at=datetime(2026, 11, 15, 9, 30, tzinfo=timezone(timedelta(hours=-3))))
```

`purpose` — NF-e only, why it is issued: `Purpose.NORMAL` (the default), `COMPLEMENTARY`, `ADJUSTMENT` or `RETURN`:

```python
from stackin import Purpose

client.issue(..., purpose=Purpose.COMPLEMENTARY, referenced_keys=["3526..."])
```

`direction` — NF-e only: `Direction.OUT` (the default) or `Direction.IN`, an incoming note the company issues itself, such as goods returned by the buyer:

```python
from stackin import Direction

client.issue(..., purpose=Purpose.RETURN, direction=Direction.IN, referenced_keys=["3526..."])
```

`referenced_keys` — NF-e only, a list of the 44-character access keys this note refers to: required for `COMPLEMENTARY` (exactly one) and, but for a few CFOPs, for `RETURN`:

```python
client.issue(..., purpose=Purpose.RETURN, referenced_keys=["35261112345678000195550010000000011000000014"])
```

### A buyer abroad (NF-e)

A `recipient_address` with `state="EX"` is a buyer outside Brazil. There `tax_id` is left out, `zip_code` and `city_code` may be left out, and `country_code` (the BACEN code, not Brazil's 1058) is required, with `country_name` beside it. The SDK does not check the BACEN code's check digit: the official table has countries whose digit does not close.

`foreign_id` — the buyer's passport or other document (5 to 20 characters), in place of a CPF/CNPJ:

```python
client.issue(..., recipient_address=Address(..., state="EX", country_code="2496", country_name="Estados Unidos"), foreign_id="P12345678")
```

`export` — an `Export` (`stackin.br`) naming where the goods leave Brazil, required for an outgoing note abroad: `exit_state` and `place`, optionally `dispatch_place`:

```python
from stackin.br import Export

client.issue(..., export=Export(exit_state="SP", place="Porto de Santos"))
```

### Fuel (NF-e)

`fuel` on a `Product` is the layout's fuel group (`comb`), needed for a fuel CFOP: `anp_code` (9 digits), `anp_description` and `consumer_state` are required; `glp_percent`, `natural_gas_national_percent`, `natural_gas_imported_percent`, `starting_value`, `codif`, `temperature_quantity` and `biodiesel_percent` are optional. It travels under the product's `fuel` key and is refused together with `extra_groups["comb"]`:

```python
from stackin.br import Fuel, Product

Product(description="Gasolina C", ncm="27101259", cfop="5656", fuel=Fuel(anp_code="320102001", anp_description="GASOLINA C COMUM", consumer_state="SP"))
```

### IBS/CBS (NF-e)

`ibs_cbs` on a `Product` is the Reforma Tributária group: `cst` (3 digits), `classification` (the 6-digit cClassTrib), `rate_state`, `rate_city` and `rate_federal` (percent) are required; `base` defaults to the item amount. `reduction_ibs` and `reduction_cbs` (0 to 100) are the cClassTrib's pRedIBS and pRedCBS — the API requires them for CST 011, 200 and 515 and refuses them for any other, so the SDK checks only the range and leaves the CST rule to the API. Left out, they are not sent:

```python
from stackin.br import IbsCbs, Product

Product(description="Arroz", ncm="10063021", cfop="5102", ibs_cbs=IbsCbs(cst="200", classification="200003", rate_state=0.1, rate_city=0.0, rate_federal=0.9, reduction_ibs=60, reduction_cbs=60))
```

## Retrying safely

Issuing is the one call you must not repeat blindly. If the response is lost — a
timeout, a dropped connection — the document may well have been authorized, and a
second attempt issues a **second** fiscal document: another credit, another number
burned, and undoing it means cancelling, which has a deadline.

Pass `idempotency_key` to make the retry safe:

```python
from decimal import Decimal

key = str(uuid.uuid4())

result = invoice.issue(
    document_type=DocumentType.NFSE,
    client_name="Maria Silva",
    tax_id="12345678909",
    items=[Product(description="Consultoria", unit_price=Decimal("1500.00"))],
    idempotency_key=key,
)
```

Retry with the **same key and the same body** and you get the first response back,
replayed — no second document, no credit consumed. `reissue()` takes the same
argument.

| Situation | What the API does |
|---|---|
| New key | issues normally, records the response |
| Same key, same body | replays the recorded response |
| Same key, different body | `APIError` 422 |
| Same key, first call still running | `APIError` 409 |
| Previous attempt failed | key is released — the retry issues |
| Key older than 24 hours | treated as new |

Generate the key yourself and keep it for as long as you might retry — a `uuid4` per
business event, not per HTTP call. The SDK never generates one, because a key minted
per call would protect nothing, and because two genuinely separate invoices for the
same customer and amount on the same day are a normal thing to issue.

## Correcting a document

Some mistakes don't need a cancellation. A wrong product name, wrong
transport details, a typo in the extra information — a **CC-e** (carta de
correção) fixes those, and it is free: no new credit, no burned series
number, no reissue.

```python
result = invoice.correct(
    "35240912345678000199550010000000011000000017",
    document_type=DocumentType.NFE,
    correction="Transportadora corrigida para Rapido Ltda",
)
```

The correction text is 15 to 1000 characters, checked locally before the call.

What a CC-e **cannot** fix: anything that changes the tax owed (base, rate,
price, quantity, totals), the buyer or the seller, or the issue date. Those
still mean cancelling and reissuing. The API sends the legally fixed wording
that says exactly this, attached to every correction.

The original document does not change — the CC-e is an event attached to it, and
the authorized XML stays as it was. A document accepts at most 20 of them, and
they are numbered for you.

**NF-e only.** NFS-e has no correction letter — cancel and reissue it instead.
The access key says which one it is: an NF-e access key is 44 characters, an
NFS-e key 50. A key that is not an NF-e access key (44 characters: digits, with
uppercase letters allowed in the first 12 positions of the issuer CNPJ, which
can be alphanumeric from July 2026) raises a `ValueError` locally, before the call:
`correct is NFe only. NFSe has no correction letter — cancel and reissue instead.`
What only the API can know stays an `APIError` with status `409`: an NF-e key
sent with `document_type=DocumentType.NFSE`, or a key for a document the API
does not hold.

## Invalidating unused numbers

NF-e numbering is sequential and the SEFAZ expects it to have no gaps. A number
gets reserved the moment issuing starts, so a submission that fails afterwards —
a rejection, a timeout — leaves a hole in the series. Reporting that range is how
you close it.

```python
result = invoice.invalidate(
    series="1",
    number_start=10,
    number_end=12,
    reason="Numeracao reservada e nao utilizada por falha no ERP",
)
```

The reason is 15 to 255 characters and the range is inclusive; both are checked
locally, as is `number_end` not being below `number_start`.

A number that already reached the authorizer can't be invalidated. The API checks
its own records first and answers `409` naming the offending numbers, without a
round trip — and the authorizer checks again for what we can't see from here.

**NF-e only**, and it takes no access key: there is no document to point at.

## Documents issued against you

Everything above serves the **issuer**. These two serve the **recipient**: what
suppliers billed to this CNPJ, and the formal answer to it.

Reading the list never calls the SEFAZ. Collecting runs on a schedule on the API
side, every six hours, and `sync_received()` asks for what is new right away. After
a read that finds nothing more, the SEFAZ makes the CNPJ wait an hour before the
next one; a sync inside that wait raises `RateLimitedError` with `code`
`DISTRIBUTION_COOLDOWN`, `retry_at` (when the wait ends) and `retry_after`
(seconds), and is refused before it reaches the SEFAZ.

The first 50 received documents a month are included in every plan; each one after
that takes R$ 0,05 from the account credit. Some existing accounts are exempt,
which `usage().received_free` tells.

```python
from stackin import Manifestation

result = client.sync_received()   # ReceivedSync: stored, pages, next_sync_at
page = client.received(limit=20)
for document in page["data"]:
    print(document["access_key"], document["issuer_name"], document["amount"])

client.manifest(access_key, manifestation=Manifestation.CIENCIA)
client.manifest(
    access_key,
    manifestation=Manifestation.OPERACAO_NAO_REALIZADA,
    reason="Mercadoria nunca chegou ao endereco",
)
```

Before you answer a document the SEFAZ sends only a **summary** (`resNFe`): access
key, issuer, amount, date. The **full document** (`nfeProc`) arrives after a
manifestation, and the `schema` field on each row says which one you hold.

The four answers are `210200` Confirmação da Operação, `210210` Ciência da
Operação, `210220` Desconhecimento da Operação and `210240` Operação não
Realizada. Only the last one takes a reason, and it requires one — both rules are
checked locally, before the request goes out, because a round trip to be told a
fixed rule is a round trip wasted.

## History and usage

`history()` lists what the company issued, newest first. `external_reference`
keeps only the documents issued with that exact reference, and `fields="summary"`
returns a lighter row per document (`items` and `fiscal_operation` left null;
`consult()` one document for its lines).

```python
page = client.history(external_reference="order-1042", fields="summary")

usage = client.usage()   # Usage, a typed model
print(usage.plan_name, usage.used_invoices, "/", usage.included_invoices)
print(usage.used_received, "/", usage.included_received, usage.received_free)
print(usage.credit_balance)   # cents
```

`usage()` reads the paying account's plan, shared by every company it holds
(`companies_on_account`). Amounts are in cents; `overage_price_cents` and
`current_period_end` may be `None`. Fields the API adds later are ignored.

## Looking up a code, or who a CNPJ belongs to

Two more clients, for the tables an issuer reads while filling a document. Neither writes anything.

```python
from stackin import FiscalReference, Taxpayer

ref = FiscalReference(api_key="...")          # country="BR" by default

ref.ncm.get("84716052")                       # one code
ref.ncm.search("teclado", limit=5)            # a page of matches
ref.cfop.get("5102")
ref.kinds()                                   # what this country has
ref.kind("ibs_cbs_class").get("000001")       # any kind, named or not
ref.search("teclado")                         # every kind at once

Taxpayer(api_key="...").get("00000000000191")
```

`cfop`, `ncm`, `cest`, `cst`, `csosn`, `iss_service`, `icms_fuel` and `ibs_cbs_class` have accessors. **`kind(name)` reaches anything else**, including a classification published after this release — ask `kinds()` rather than trusting this list.

`metadata` is passed through as the API sends it and differs per kind: `utrib` on an NCM, `ncm_code` on a CEST, `tax_type` on a CST, `None` on an ISS service.

Three things worth knowing before you loop:

- **These share the invoice read allowance** — 600 calls a minute per key, the same bucket `consult()`, `history()`, `received()` and `pdf()` draw from. One `search()` page beats N `get()` calls.
- **Ordering is fixed** (kind, then code, ascending). Unlike `history()`, these take no `sort_by`/`order_by`.
- **A 404 from `Taxpayer` does not mean the company does not exist.** That registry reloads monthly, so a recently registered CNPJ is simply not in it yet. Do not build a validation rule on it.

`Taxpayer` has one method and keeps one: the registry holds the names and addresses of real people, so there is no search over it, by design.

## Saved clients

The company keeps the recipients it issues to. A successful issuance saves a new
recipient on its own; `Clients` reads and edits them, and `issue(client_id=...)`
issues to one without retyping it.

```python
from stackin import ClientAlreadyExistsError, Clients, DocumentType, Invoice

clients = Clients(api_key="...")

page = clients.list(search="acme", limit=20)        # active ones, by name
clients.list(is_active=False)                       # the deactivated ones
clients.list(source="issued", sort_by="uses_count", order_by="desc")

try:
    acme = clients.create(name="ACME Ltda", tax_id="11.222.333/0001-81",
                          email="nf@acme.test")
except ClientAlreadyExistsError as error:
    acme = clients.get(error.client_id)            # it was there already

clients.update(acme["id"], phone="+5511999999999", notes=None)  # None clears
clients.deactivate(acme["id"])                      # kept, hidden from list()
clients.reactivate(acme["id"])

Invoice(api_key="...").issue(
    document_type=DocumentType.NFSE,
    client_id=acme["id"],                           # name, tax_id, address from it
    items=[...],
)
```

- `list()` filters by `search` (part of the name, the tax id masked or not, or the
  `foreign_id`), `source` (`manual`, `issued`, `issuance`) and `is_active` (the API
  lists active clients when it is left out), and pages with `limit`/`offset`.
  `sort_by` takes `name`, `last_used_at`, `created_at` or `uses_count`.
- `update()` sends only the fields passed; `address` replaces the whole address. The
  API checks the client as a whole, so clearing a Brazilian client's `tax_id` is
  refused like a create without one.
- On `issue()`, the client fills whichever of `client_name`, `tax_id`, `foreign_id`
  and `recipient_address` are left out; the ones passed win. With `client_id` none
  of those four is required by the SDK: the API checks the merged request. A
  deactivated client is refused there (422) until it is reactivated.
- `update_client=True` on `issue()` rewrites an existing client with that request's
  recipient data. Left out, the issuance only counts one more use of it.
- Reading needs `invoice:read`; creating, editing and deactivating need
  `invoice:issue`. `company` works here as everywhere else.

## Several companies

An API key belongs to one company and needs none of this. An OAuth credential may
cover several, each with its own permissions; name the one a request acts on with
`company` — its UUID or its CNPJ, punctuation or not. It goes out as the
`X-Stackin-Company` header. Left unset, nothing is sent and requests are exactly
what they were before.

```python
from stackin import Invoice

client = Invoice(api_key="...", company="11.222.333/0001-81")  # every request
client.history(company="6f1c2a9e-...")                         # this call only

client.companies()
# {"environment": "production",
#  "companies": [{"company_id": "...", "name": "...", "tax_id": "...",
#                 "permissions": ["invoice:read", ...]}]}
```

`companies()` lists what the credential covers and what it may do in each.
`FiscalReference` and `Taxpayer` take `company` too and send it on every lookup;
the API ignores it there.

## Errors

- `stackin.APIError` — the API responded with a non-2xx status (`status_code`, `detail`) — a 401 here means `api_key` is missing, wrong, or was rotated.
- `stackin.CompanyRequiredError` (an `APIError`, 422) — the credential covers several companies and none was named. `companies` lists them.
- `stackin.CompanyNotInScopeError` (an `APIError`, 403) — the named company is not one the credential covers. `companies` lists the ones it does.
- `stackin.InsufficientPermissionError` (an `APIError`, 403) — the credential reaches the company but lacks the permission; `description` reads `needs X, has Y, company=<id>`. None of the three is worth retrying as is.
- `stackin.ClientAlreadyExistsError` (an `APIError`, 409) — `Clients.create()` or `update()` with a `tax_id` or `foreign_id` the company already has on another client. `client_id` names that client.
- `stackin.ClientInactiveError` (an `APIError`, 422) — `issue()` with the `client_id` of a deactivated client. `client_id` names it; `Clients.reactivate()` brings it back.
- `stackin.ClientNotFoundError` (an `APIError`, 404) — no client of this company has that `client_id`.
- `stackin.PaymentRequiredError` (an `APIError`, 402) — the account has no allowance or credit left for the call; `detail` says what ran out.
- `stackin.RateLimitedError` (an `APIError`, 429) — too many calls, or the SEFAZ's one-hour wait on received documents. `retry_after` is the `Retry-After` header in seconds, `code` names the limit (`DISTRIBUTION_COOLDOWN`) and `retry_at` the moment the wait ends; each is `None` when the response does not carry it.
- `stackin.ConnectionFailedError` — the API didn't respond (network/DNS/timeout).
- `ValueError` — `issue()` without `client_name` or `tax_id` and no `client_id` (`tax_id` may be left out for an NF-e to a buyer abroad), `items` is empty, missing `ncm`/`cfop` on an item for NFE, an item `description` over 120 characters on NFE (the `xProd` limit; NFSE has no such limit), any string in an NFE request with a character the NF-e cannot carry (outside ISO-8859-1, latin1: an emoji, CJK, Cyrillic…; the error names the field — typographic quotes, dashes, ellipsis, bullet, `€` and `™` are not refused, the API converts them and folds tabs and line breaks into a space), a missing/incomplete `recipient_address` on NFE, or a missing/incomplete `recipient_address` (every field except `city_code`) on NFSE when any item has `tax_retained=True` (the ISSQN retained by the tomador).
- `ValueError` — `correct()` with a key that is not an NF-e access key (44 characters): a correction letter exists only on NF-e; an NFS-e is cancelled and reissued instead. An NF-e key sent with `DocumentType.NFSE`, or one the API does not hold, is an `APIError` 409, not a `ValueError`.
- `pydantic.ValidationError` (a `ValueError`) — a model built with a value the NF-e 4.00 XSD refuses: an `ncm` that is not 8 digits (or `00` for a service line), a `barcode` that is not `SEM GTIN` or an 8/12/13/14-digit GTIN with a valid GS1 check digit, a `recopi_number` that is not 20 digits with valid check digits, or an `Address` `street`/`neighborhood` under 2 characters once trimmed.

Building the full fiscal document (issuer data, service code, tax groups, schema-accurate XML) is the API's job — configured once per company, not passed on every call.

## Examples

Runnable end-to-end scripts in [`examples/nfe/`](examples/nfe/) and [`examples/nfse/`](examples/nfse/) — one file per field/variant, from the bare minimum to every field filled. `examples/consult_invoice.py`, `examples/cancel_invoice.py`, and `examples/reissue_invoice.py` cover the operations that act on an already-issued document. `examples/lookup_fiscal_reference.py` and `examples/lookup_taxpayer.py` cover the two read-only clients.
