"""Address module."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class Address(BaseModel):
    """A plain postal address."""

    state: str | None = Field(default=None)
    city_code: str | None = Field(default=None)
    street: str | None = Field(default=None)
    number: str | None = Field(default=None)
    neighborhood: str | None = Field(default=None)
    city: str | None = Field(default=None)
    zip_code: str | None = Field(default=None)

    @field_validator("street", "neighborhood")
    @classmethod
    def _at_least_two_characters(cls, value: str | None, info) -> str | None:
        """The NF-e XSD sets xLgr and xBairro at 2 characters minimum."""
        if value is not None and len(value.strip()) < 2:
            raise ValueError(
                f"{info.field_name} must have at least 2 characters"
            )
        return value

    def to_dict(self) -> dict:
        """Returns the address as a plain dict."""
        return self.model_dump(exclude_none=True)
