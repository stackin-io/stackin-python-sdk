"""NF-e sale terms: presence, intermediary, freight and payment."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, field_serializer, model_validator

Presence = Literal["0", "1", "2", "3", "5", "9"]
FreightMode = Literal["0", "1", "2", "3", "4", "9"]
CardIntegration = Literal["1", "2"]

PRESENCES = ("0", "1", "2", "3", "5", "9")
FREIGHT_MODES = ("0", "1", "2", "3", "4", "9")
PAYMENT_METHODS = frozenset(
    "01 02 03 04 05 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 90 91 99".split()
)
CARD_METHODS = frozenset({"03", "04", "10", "11", "12", "13", "15", "17", "18"})
CARD_BRANDS = frozenset([f"{code:02d}" for code in range(1, 28)] + ["99"])
CHANGE_MAX = Decimal("300000.00")
PAYMENTS_MAX = 100

_MONEY_MAX = Decimal("9999999999999.99")


def _money(value: Decimal) -> str:
    return f"{value:.2f}"


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

    quantity: int | None = Field(default=None, ge=0, lt=10**15)
    species: str | None = Field(default=None, min_length=1, max_length=60)
    brand: str | None = Field(default=None, min_length=1, max_length=60)
    numbering: str | None = Field(default=None, min_length=1, max_length=60)
    net_weight: Decimal | None = Field(default=None, ge=0)
    gross_weight: Decimal | None = Field(default=None, ge=0)

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
    volumes: list[TransportVolume] | None = Field(default=None, max_length=5000)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"freight_mode": self.freight_mode}
        if self.volumes is not None:
            data["volumes"] = [volume.to_dict() for volume in self.volumes]
        return data


class PaymentCard(BaseModel):
    """`card`: the electronic payment's processor and authorization."""

    integration: CardIntegration
    tax_id: str | None = Field(default=None)
    brand: str | None = Field(default=None)
    authorization: str | None = Field(default=None, min_length=1, max_length=128)

    @model_validator(mode="after")
    def _rules(self) -> PaymentCard:
        if self.brand is not None and self.brand not in CARD_BRANDS:
            raise ValueError(f"brand {self.brand!r} is not in the card brand table")
        if self.integration == "1" and not (self.tax_id and self.authorization):
            raise ValueError("integration 1 requires tax_id and authorization")
        return self

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class Payment(BaseModel):
    """One `detPag`: how much was paid and how.

    `method` is the national tPag code; 99 (other) needs `description`.
    `card` goes only with the card and instant-payment methods.
    """

    method: str
    amount: Decimal = Field(ge=0, le=_MONEY_MAX, decimal_places=2)
    description: str | None = Field(default=None, min_length=2, max_length=60)
    card: PaymentCard | None = Field(default=None)

    @field_serializer("amount")
    def _amount(self, value: Decimal) -> str:
        return _money(value)

    @model_validator(mode="after")
    def _rules(self) -> Payment:
        if self.method not in PAYMENT_METHODS:
            raise ValueError(
                f"method {self.method!r} is not in the national payment method table"
            )
        if self.method == "99" and self.description is None:
            raise ValueError("description is required for method 99")
        if self.card is not None and self.method not in CARD_METHODS:
            raise ValueError(f"card does not go with method {self.method}")
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


def validate_change(change: Decimal) -> Decimal:
    if change < 0 or change > CHANGE_MAX:
        raise ValueError(f"change must be between 0 and {CHANGE_MAX}")
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
        body["change"] = _money(validate_change(Decimal(change)))
    return body
