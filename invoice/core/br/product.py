"""Product module."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, Field

from invoice.core.br.tax import Tax


class PresumedCredit(BaseModel):
    """A presumed tax credit applied to this item."""

    code: str = Field(pattern=r"^[\x21-\xff]{8}$|^[\x21-\xff]{10}$")
    percentage: float
    amount: float


_CBENEF_PATTERN = r"^(SEM CBENEF|[\x21-\xff]{8}|[\x21-\xff]{10})$"


class Product(BaseModel):
    """One product or service line item on an invoice."""

    description: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    ncm: str | None = Field(default=None, pattern=r"^\d{2}$|^\d{8}$")
    cfop: str | None = Field(default=None, pattern=r"^[123567]\d{3}$")
    unit: str = Field(default="UN")
    quantity: float = Field(default=1.0, gt=0)
    barcode: str | None = Field(default=None)
    cest: str | None = Field(default=None, pattern=r"^\d{7}$")
    nve_codes: list[Annotated[str, Field(pattern=r"^[A-Z]{2}\d{4}$")]] | None = Field(
        default=None
    )
    ind_escala: str | None = Field(default=None)
    manufacturer_cnpj: str | None = Field(
        default=None, pattern=r"^[0-9A-Z]{12}\d{2}$"
    )
    tax_benefit_code: str | None = Field(default=None, pattern=_CBENEF_PATTERN)
    presumed_credits: list[PresumedCredit] | None = Field(default=None)
    ex_tipi: str | None = Field(default=None, pattern=r"^\d{2,3}$")
    freight: float | None = Field(default=None)
    insurance: float | None = Field(default=None)
    discount: float | None = Field(default=None)
    other_expenses: float | None = Field(default=None)
    used_movable_asset: bool = Field(default=False)
    purchase_order: str | None = Field(default=None)
    purchase_order_item: str | None = Field(default=None, pattern=r"^\d{1,6}$")
    import_content_control_number: str | None = Field(
        default=None,
        pattern=r"^[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}$",
    )
    recopi_number: str | None = Field(default=None, pattern=r"^\d{20}$")
    extra_groups: dict[str, Any] | None = Field(default=None)
    tax: Tax | dict[str, Any] | None = Field(default=None)

    def to_dict(self) -> dict:
        """Returns the item as a plain dict, ready for the request body."""
        data = self.model_dump(
            exclude_none=True, exclude={"description", "amount", "tax"}
        )
        if isinstance(self.tax, Tax):
            data["tax"] = self.tax.to_dict()
        elif self.tax is not None:
            data["tax"] = self.tax
        return {"description": self.description, "amount": self.amount, "product": data}
