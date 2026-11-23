"""NF-e sale terms: presence, intermediary, freight and payment."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, field_serializer, model_validator

Presence = Literal["0", "1", "2", "3", "4", "5", "9"]
FreightMode = Literal["0", "1", "2", "3", "4", "9"]

PRESENCES = ("0", "1", "2", "3", "4", "5", "9")
FREIGHT_MODES = ("0", "1", "2", "3", "4", "9")
PAYMENT_METHOD_PATTERN = re.compile(r"\d{2}")
PAYMENTS_MAX = 100


def _money(value: Decimal) -> str:
    return format(value, "f")


class Intermediary(BaseModel):
    """The marketplace or platform the sale went through (`infIntermed`)."""

    tax_id: str = Field(description="CNPJ of the intermediary.")
    identifier: str = Field(
        min_length=2,
        max_length=60,
        description="The seller's user name or profile id at the intermediary.",
    )

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class TransportVolume(BaseModel):
    """One `transp/vol` group: packages carried and their weight in kg."""

    quantity: int | None = None
    species: str | None = None
    brand: str | None = None
    numbering: str | None = None
    net_weight: Decimal | None = Field(default=None, ge=0, decimal_places=3)
    gross_weight: Decimal | None = Field(default=None, ge=0, decimal_places=3)

    @field_serializer("net_weight", "gross_weight")
    def _weight(self, value: Decimal | None) -> str | None:
        return None if value is None else format(value, "f")

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class Transport(BaseModel):
    """`transp`: who arranges the freight, and the volumes carried.

    `volumes` left as None is left out, and the API writes one volume
    from the lines' weights when they carry them; an empty list writes
    none.
    """

    freight_mode: FreightMode
    volumes: list[TransportVolume] | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"freight_mode": self.freight_mode}
        if self.volumes is not None:
            data["volumes"] = [volume.to_dict() for volume in self.volumes]
        return data


class PaymentCard(BaseModel):
    """`card`: the electronic payment's processor and authorization."""

    integration: str
    tax_id: str | None = None
    brand: str | None = None
    authorization: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class Payment(BaseModel):
    """One `detPag`: how much was paid and how.

    `method` is the national tPag code; 99 (other) needs `description`.
    """

    method: str
    amount: Decimal = Field(ge=0, decimal_places=2)
    description: str | None = None
    card: PaymentCard | None = None

    @model_validator(mode="after")
    def _rules(self) -> Payment:
        if not PAYMENT_METHOD_PATTERN.fullmatch(self.method):
            raise ValueError(f"method {self.method!r} is not a 2-digit tPag code")
        if self.method == "99" and self.description is None:
            raise ValueError("description is required for method 99")
        return self

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"method": self.method, "amount": _money(self.amount)}
        if self.description is not None:
            data["description"] = self.description
        if self.card is not None:
            data["card"] = self.card.to_dict()
        return data


class SaleTerms(BaseModel):
    """The sale terms an invoice was issued with, as the detail returns them.

    Each is None when none was sent. Build one from the invoice dict with
    `SaleTerms.from_invoice()`.
    """

    presence: str | None = None
    intermediary: Intermediary | None = None
    transport: Transport | None = None
    payments: list[Payment] | None = None
    change: Decimal | None = None

    @classmethod
    def from_invoice(cls, invoice: dict[str, Any]) -> SaleTerms:
        return cls.model_validate(invoice)


def validate_presence(presence: str) -> str:
    if presence not in PRESENCES:
        raise ValueError(f"presence {presence!r} must be one of {', '.join(PRESENCES)}")
    return presence


def _check_change(change: Decimal) -> Decimal:
    if change < 0:
        raise ValueError("change must be 0 or more")
    if change != change.quantize(Decimal("0.01")):
        raise ValueError("change takes at most 2 decimal places")
    return change


def terms_payload(
    *,
    presence: str | None,
    intermediary: Intermediary | None,
    transport: Transport | None,
    payments: list[Payment] | None,
    change: Decimal | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {}
    if presence is not None:
        body["presence"] = validate_presence(presence)
    if intermediary is not None:
        body["intermediary"] = intermediary.to_dict()
    if transport is not None:
        body["transport"] = transport.to_dict()
    if payments is not None:
        if not 1 <= len(payments) <= PAYMENTS_MAX:
            raise ValueError(f"payments takes 1 to {PAYMENTS_MAX} entries")
        body["payments"] = [payment.to_dict() for payment in payments]
    if change is not None:
        body["change"] = _money(_check_change(Decimal(change)))
    return body
