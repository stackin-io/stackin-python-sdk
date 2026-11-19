"""What the account's plan allows, and what one read of received documents brought.

Both are typed because their fields are fixed and numeric: a caller
compares used_invoices against included_invoices, not keys of a dict.
Fields the API adds later are ignored rather than refused, so an older
SDK keeps reading a newer API.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Usage(BaseModel):
    """The plan behind the company and how much of it is used.

    The numbers are the paying account's, shared by every company it
    holds; `companies_on_account` says whether that sharing is real.
    Amounts are in cents. Received documents: the first
    `included_received` a month are included, then each one costs
    `received_price_cents` from `credit_balance`, unless
    `received_free` exempts the account.
    """

    model_config = ConfigDict(extra="ignore")

    plan_name: str
    plan_slug: str
    included_invoices: int
    used_invoices: int
    overage_price_cents: int | None
    included_received: int = 50
    used_received: int = 0
    received_price_cents: int = 5
    received_free: bool = False
    current_period_start: datetime
    current_period_end: datetime | None
    credit_balance: int
    companies_on_account: int


class ReceivedSync(BaseModel):
    """What one read of the SEFAZ's distribution brought back.

    `next_sync_at` is set when the SEFAZ had nothing more to deliver:
    no read is allowed before it (UTC).
    """

    model_config = ConfigDict(extra="ignore")

    stored: int
    pages: int
    last_nsu: str
    max_nsu: str | None = None
    next_sync_at: datetime | None = None
