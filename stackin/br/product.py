"""Product module."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, Field, field_validator, model_validator

from stackin.br.tax import Tax


class IbsCbs(BaseModel):
    """The Reforma Tributária group for one item."""

    cst: str = Field(pattern=r"^\d{3}$")
    classification: str = Field(pattern=r"^\d{6}$")
    base: float | None = Field(default=None, gt=0)
    rate_state: float = Field(ge=0)
    rate_city: float = Field(ge=0)
    rate_federal: float = Field(ge=0)
    reduction_ibs: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description=(
            "pRedAliq of the IBS (state and municipality), percent: the "
            "cClassTrib's pRedIBS in the official classification table. "
            "Required for CST 011, 200 and 515, refused for any other."
        ),
    )
    reduction_cbs: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description=(
            "pRedAliq of the CBS, percent: the cClassTrib's pRedCBS. "
            "Required for CST 011, 200 and 515, refused for any other."
        ),
    )


class PresumedCredit(BaseModel):
    """A presumed tax credit applied to this item."""

    code: str = Field(pattern=r"^[\x21-\xff]{8}$|^[\x21-\xff]{10}$")
    percentage: float
    amount: float


class Fuel(BaseModel):
    """The NF-e fuel group (`comb`), needed for a fuel CFOP.

    Groups it does not cover (CIDE, encerrante, origComb) still go
    through `extra_groups["comb"]`, but never together with this one.
    """

    anp_code: str = Field(pattern=r"^[0-9]{9}$", description="cProdANP.")
    anp_description: str = Field(min_length=2, max_length=95, description="descANP.")
    consumer_state: str = Field(
        pattern=r"^[A-Z]{2}$", description="UFCons, where it is consumed."
    )
    glp_percent: float | None = Field(
        default=None, ge=0, le=100, description="pGLP, GLP only."
    )
    natural_gas_national_percent: float | None = Field(
        default=None, ge=0, le=100, description="pGNn, GLP only."
    )
    natural_gas_imported_percent: float | None = Field(
        default=None, ge=0, le=100, description="pGNi, GLP only."
    )
    starting_value: float | None = Field(
        default=None, ge=0, description="vPart, GLP only."
    )
    codif: str | None = Field(
        default=None, pattern=r"^[0-9]{1,21}$", description="CODIF."
    )
    temperature_quantity: float | None = Field(
        default=None, ge=0, description="qTemp, at 20 degrees Celsius."
    )
    biodiesel_percent: float | None = Field(
        default=None, ge=0, le=100, description="pBio."
    )


_CBENEF_PATTERN = r"^(SEM CBENEF|[\x21-\xff]{8}|[\x21-\xff]{10})$"

_BR_FIELDS = {
    "ncm",
    "cfop",
    "cest",
    "nve_codes",
    "ind_escala",
    "manufacturer_cnpj",
    "tax_benefit_code",
    "presumed_credits",
    "ex_tipi",
    "import_content_control_number",
    "recopi_number",
    "extra_groups",
    "ibs_cbs",
    "tax",
    "fuel",
}


def _gtin_check_digit_ok(gtin: str) -> bool:
    """GS1 modulo 10: weights 3,1,3,1... from the right, check excluded."""
    body = gtin[-2::-1]
    total = sum(
        int(digit) * (3 if index % 2 == 0 else 1) for index, digit in enumerate(body)
    )
    return (10 - total % 10) % 10 == int(gtin[-1])


def _recopi_check_digit(digits: str) -> int:
    """MOC 8.5 modulo 11: weights n..1 left to right; remainder 0 or 1 gives 0."""
    weights = range(len(digits), 0, -1)
    total = sum(int(digit) * weight for digit, weight in zip(digits, weights))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder


def _recopi_check_digits_ok(recopi: str) -> bool:
    """DV1 over the first 18 digits, DV2 over those 18 plus DV1."""
    dv1 = _recopi_check_digit(recopi[:18])
    dv2 = _recopi_check_digit(recopi[:18] + str(dv1))
    return recopi[18:] == f"{dv1}{dv2}"


def _decimal_str(value: Decimal | None) -> str | None:
    """JSON has no decimal; a float would lose the tenth place."""
    return None if value is None else format(value, "f")


class Product(BaseModel):
    """One product or service line item on an invoice."""

    description: str | None = Field(
        default=None,
        min_length=1,
        description="Required unless item_id names a catalog item.",
    )
    item_id: str | None = Field(
        default=None,
        description=(
            "A catalog item (see Items): it fills whatever this line "
            "leaves out, and what the line sends wins."
        ),
    )
    amount: Decimal | None = Field(default=None, gt=0)
    unit_price: Decimal | None = Field(default=None, gt=0)
    unit: str = Field(default="UN")
    quantity: float = Field(default=1.0, gt=0)
    barcode: str | None = Field(
        default=None,
        pattern=r"^(SEM GTIN|\d{8}|\d{12,14})$",
        description="cEAN: a GTIN-8/12/13/14, or SEM GTIN.",
    )
    freight: float | None = Field(default=None)
    insurance: float | None = Field(default=None)
    discount: float | None = Field(default=None)
    other_expenses: float | None = Field(default=None)
    used_movable_asset: bool = Field(default=False)
    purchase_order: str | None = Field(default=None)
    purchase_order_item: str | None = Field(default=None, pattern=r"^\d{1,6}$")

    ncm: str | None = Field(
        default=None,
        pattern=r"^(00|\d{8})$",
        description=(
            "The full 8 digits, or 00 for a service line. Any other "
            "short code the SEFAZ rejects with 777."
        ),
    )
    cfop: str | None = Field(default=None, pattern=r"^[123567]\d{3}$")
    cest: str | None = Field(default=None, pattern=r"^\d{7}$")
    nve_codes: list[Annotated[str, Field(pattern=r"^[A-Z]{2}\d{4}$")]] | None = Field(
        default=None
    )
    ind_escala: str | None = Field(default=None)
    manufacturer_cnpj: str | None = Field(default=None, pattern=r"^[0-9A-Z]{12}\d{2}$")
    tax_benefit_code: str | None = Field(default=None, pattern=_CBENEF_PATTERN)
    presumed_credits: list[PresumedCredit] | None = Field(default=None)
    ex_tipi: str | None = Field(default=None, pattern=r"^\d{2,3}$")
    import_content_control_number: str | None = Field(
        default=None,
        pattern=(r"^[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}" r"-[A-F0-9]{4}-[A-F0-9]{12}$"),
    )
    recopi_number: str | None = Field(
        default=None,
        description="nRECOPI: 20 digits, the last two modulo-11 check digits.",
    )
    ibs_cbs: IbsCbs | None = Field(default=None)
    extra_groups: dict[str, Any] | None = Field(default=None)
    tax: Tax | dict[str, Any] | None = Field(default=None)
    fuel: Fuel | None = Field(
        default=None, description="The fuel group (comb), NF-e only."
    )

    service_code: str | None = Field(
        default=None, description="LC 116/2003 item.subitem, nfse only."
    )
    service_discount: float | None = Field(
        default=None, description="Unconditional discount, nfse only."
    )
    tax_retained: bool = Field(
        default=False, description="ISSQN retained by the tomador, nfse only."
    )
    observations: str | None = Field(
        default=None, max_length=2000, description="nfse only."
    )

    @field_validator("barcode")
    @classmethod
    def _valid_gtin_check_digit(cls, value: str | None) -> str | None:
        """Runs after the pattern: SEM GTIN or digits by now."""
        if value is None or not value.isdigit():
            return value
        if not _gtin_check_digit_ok(value):
            raise ValueError("barcode has an invalid GTIN check digit")
        return value

    @field_validator("recopi_number")
    @classmethod
    def _valid_recopi_check_digits(cls, value: str | None) -> str | None:
        """The date/time part is not checked; it depends on the clock."""
        if value is None:
            return value
        if len(value) != 20 or not (value.isascii() and value.isdigit()):
            raise ValueError("recopi_number must have exactly 20 digits")
        if not _recopi_check_digits_ok(value):
            raise ValueError("recopi_number has invalid check digits")
        return value

    @model_validator(mode="after")
    def _description_or_item(self) -> Product:
        """Without a catalog item there is nothing to fill it from."""
        if self.description is None and self.item_id is None:
            raise ValueError("description is required unless item_id is given")
        return self

    @model_validator(mode="after")
    def _one_fuel_group(self) -> Product:
        """The API refuses the comb group sent twice."""
        if self.fuel is not None and "comb" in (self.extra_groups or {}):
            raise ValueError("send the fuel group once: fuel or extra_groups['comb']")
        return self

    def to_dict(self) -> dict:
        """Returns the item as a plain dict, ready for the request body."""
        _NFSE_FIELDS = {
            "service_code",
            "service_discount",
            "tax_retained",
            "observations",
        }
        data = self.model_dump(
            exclude_none=True,
            exclude={
                "description",
                "item_id",
                "amount",
                "unit_price",
                "tax",
                *_BR_FIELDS,
                *_NFSE_FIELDS,
            },
        )
        br = self.model_dump(exclude_none=True, include=_BR_FIELDS - {"tax"})
        if isinstance(self.tax, Tax):
            br["tax"] = self.tax.to_dict()
        elif self.tax is not None:
            br["tax"] = self.tax
        if br:
            data["br"] = br
        # With a catalog item, a default the caller did not set must not
        # override what the catalog holds (its unit, its iss_retained).
        # A value the caller did set is still sent, False included.
        from_catalog = self.item_id is not None
        if from_catalog and "unit" not in self.model_fields_set:
            data.pop("unit", None)
        line: dict[str, Any] = {}
        if self.item_id is not None:
            line["item_id"] = self.item_id
        if self.description is not None:
            line["description"] = self.description
        result = {
            **line,
            "amount": _decimal_str(self.amount),
            "unit_price": _decimal_str(self.unit_price),
            "product": data,
            "service_code": self.service_code,
            "discount": self.service_discount,
            "tax_retained": self.tax_retained,
            "observations": self.observations,
        }
        if from_catalog and "tax_retained" not in self.model_fields_set:
            del result["tax_retained"]
        return result
