"""Export module."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Export(BaseModel):
    """Where the goods leave Brazil: the NF-e `exporta` group.

    Required by the API for an outgoing NF-e to a buyer abroad
    (recipient_address.state EX), refused otherwise.
    """

    exit_state: str = Field(
        min_length=2,
        max_length=2,
        description="UFSaidaPais: the Brazilian state the goods leave from.",
    )
    place: str = Field(
        min_length=1,
        max_length=60,
        description="xLocExporta: place of shipment or border crossing.",
    )
    dispatch_place: str | None = Field(
        default=None,
        min_length=1,
        max_length=60,
        description="xLocDespacho: customs facility of dispatch.",
    )

    def to_dict(self) -> dict:
        """Returns the group as a plain dict, unset fields left out."""
        return self.model_dump(exclude_none=True)
