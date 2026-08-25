"""Product module — Brazil-specific, see `invoice.core.br`."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Product(BaseModel):
    """
    Product/item details for a Brazilian NFE — **not** a generic
    "line item" concept. `ncm`/`cfop` are Brazilian tax classification
    codes (Receita Federal's NCM table, SINIEF's CFOP table) with no
    equivalent in NFSE or in any other country's fiscal documents —
    don't reuse this class outside a Brazil/NFE context.

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
