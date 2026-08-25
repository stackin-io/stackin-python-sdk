"""Address module."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Address(BaseModel):
    """
    Picks an authorizer/routing target for `issue()` — despite the
    name, only `state`/`city_code` are read; the rest of the fields
    aren't sent anywhere yet. Used twice, with different meanings:
    `address` (the issuer's own UF/city — not the issuer's real
    address either, that comes from invoice-api's own config) and
    `recipient_address` (the actual customer's state, used for
    `idDest`).

    `issue()` only reads `state` (NFE) or `city_code` (NFSE) from
    this — everything else is optional, fill in only what you have.

    Args:
        state (str | None): Two-letter state code (e.g. "SP") —
            required for NFE.
        city_code (str | None): IBGE city code — required for NFSE.
        street (str | None): Street name.
        number (str | None): Street number.
        neighborhood (str | None): Neighborhood.
        city (str | None): City name.
        zip_code (str | None): ZIP code, digits only.
    """

    state: str | None = Field(default=None)
    city_code: str | None = Field(default=None)
    street: str | None = Field(default=None)
    number: str | None = Field(default=None)
    neighborhood: str | None = Field(default=None)
    city: str | None = Field(default=None)
    zip_code: str | None = Field(default=None)

    def to_dict(self) -> dict:
        """Return the address as a plain dict, ready for the request
        body — fields left unset are omitted, not sent as null."""
        return self.model_dump(exclude_none=True)
