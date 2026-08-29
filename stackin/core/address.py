"""Address module."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Address(BaseModel):
    """A plain postal address."""

    state: str | None = Field(default=None)
    city_code: str | None = Field(default=None)
    street: str | None = Field(default=None)
    number: str | None = Field(default=None)
    neighborhood: str | None = Field(default=None)
    city: str | None = Field(default=None)
    zip_code: str | None = Field(default=None)

    def to_dict(self) -> dict:
        """Returns the address as a plain dict."""
        return self.model_dump(exclude_none=True)
