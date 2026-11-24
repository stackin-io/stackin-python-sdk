"""Address module."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator


class Address(BaseModel):
    """A plain postal address. State EX is a buyer abroad, NF-e only."""

    state: str | None = Field(default=None)
    city_code: str | None = Field(default=None)
    street: str | None = Field(default=None)
    number: str | None = Field(default=None)
    neighborhood: str | None = Field(default=None)
    city: str | None = Field(default=None)
    zip_code: str | None = Field(default=None)
    country_code: str | None = Field(
        default=None,
        pattern=r"^[0-9]{1,4}$",
        description=(
            "BACEN country code, 1 to 4 digits. Required, and not 1058, when "
            "state is EX. Its check digit is not verified: the official "
            "table has countries whose digit does not close."
        ),
    )
    country_name: str | None = Field(default=None)
    country_iso2: str | None = Field(
        default=None,
        pattern=r"^[A-Z]{2}$",
        description=(
            "ISO 3166 alpha-2 country code, NFS-e only: the code a "
            "recipient abroad (state EX) takes instead of country_code."
        ),
    )
    postal_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=11,
        description="Postal code abroad, NFS-e only.",
    )
    province: str | None = Field(
        default=None,
        min_length=1,
        max_length=60,
        description="State, province or region abroad, NFS-e only.",
    )
    complement: str | None = Field(
        default=None,
        description=(
            "Apartment, suite or block. One the document cannot carry is "
            "left out by the API with the warning RECIPIENT_COMPLEMENT_OMITTED."
        ),
    )
    state_registration: str | None = Field(
        default=None,
        description=(
            "Recipient's IE (inscrição estadual), NF-e only. Send it for a "
            "recipient registered as an ICMS contributor; ISENTO for an "
            "exempt one; leave it out for a non-contributor."
        ),
    )

    @field_validator("state_registration")
    @classmethod
    def _state_registration(cls, value: str | None) -> str | None:
        """Digits (mask dropped) or ISENTO, as the API takes it."""
        if value is None:
            return None
        cleaned = re.sub(r"[\s./-]", "", value).upper()
        if cleaned != "ISENTO" and not re.fullmatch(r"[0-9]{2,14}", cleaned):
            raise ValueError("state_registration takes 2 to 14 digits, or ISENTO")
        return cleaned

    @field_validator("street", "neighborhood")
    @classmethod
    def _at_least_two_characters(cls, value: str | None, info) -> str | None:
        """The NF-e XSD sets xLgr and xBairro at 2 characters minimum."""
        if value is not None and len(value.strip()) < 2:
            raise ValueError(f"{info.field_name} must have at least 2 characters")
        return value

    def to_dict(self) -> dict:
        """Returns the address as a plain dict."""
        return self.model_dump(exclude_none=True)
