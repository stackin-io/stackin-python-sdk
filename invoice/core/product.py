"""Product module."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Product(BaseModel):
    """
    Product/item details — NFE only, NFSE ignores this entirely (a
    service has no NCM/CFOP/unit).

    `issue()` requires `ncm` and `cfop` when `document_type` is NFE.

    Args:
        ncm (str | None): NCM code (8 digits, or "00" for services/
            non-goods).
        cfop (str | None): CFOP code for this operation.
        unit (str): Commercial unit. Default "UN".
        quantity (float): Commercial quantity. Default 1 (the unit
            price is then just `amount`).
    """

    ncm: str | None = Field(default=None)
    cfop: str | None = Field(default=None)
    unit: str = Field(default="UN")
    quantity: float = Field(default=1.0, gt=0)

    def to_dict(self) -> dict:
        """Return the product as a plain dict, ready for the request
        body — fields left unset are omitted, not sent as null."""
        return self.model_dump(exclude_none=True)
