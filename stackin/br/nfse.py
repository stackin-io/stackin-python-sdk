"""NFS-e document-level fields: the `nfse` object of an issuance.

Every model refuses unknown fields, as the API does, and checks only the
shape each field has by itself: patterns, lengths, ranges and code sets.
What one field means for another (one shape out of several, the MEI and
Simples rules, the layout of each environment) is the API's, answered as
an APIError.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

PERCENT_MAX = Decimal("100")
SIMPLES_PERCENT_MAX = Decimal("99.99")
ISS_RATE_MAX = Decimal("5")
AMOUNT_MAX = Decimal("999999999999999.99")
NFSE_KEY_PATTERN = r"^[0-9]{6}[0-9A-Z]{14}[0-9]{30}$"
NFE_KEY_PATTERN = r"^[0-9]{6}[0-9A-Z]{14}[0-9]{24}$"

PisCofinsCst = Literal[
    "00",
    "01",
    "02",
    "03",
    "04",
    "05",
    "06",
    "07",
    "08",
    "09",
    "49",
    "50",
    "51",
    "52",
    "53",
    "54",
    "55",
    "56",
    "60",
    "61",
    "62",
    "63",
    "64",
    "65",
    "66",
    "67",
    "70",
    "71",
    "72",
    "73",
    "74",
    "75",
    "98",
    "99",
]

DEDUCTION_TYPES = (1, 2, 3, 4, 5, 6, 7, 8, 9, 99, 101, 102, 103, 104, 105, 199)
DeductionType = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 99, 101, 102, 103, 104, 105, 199]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    def to_dict(self) -> dict[str, Any]:
        """The model as the request body takes it: decimals and dates as
        strings, unset fields left out."""
        return self.model_dump(mode="json", exclude_none=True)


def _percent(description: str, maximum: Decimal = PERCENT_MAX) -> Any:
    return Field(
        default=None, ge=0, le=maximum, decimal_places=2, description=description
    )


def _amount(description: str) -> Any:
    return Field(
        default=None, ge=0, le=AMOUNT_MAX, decimal_places=2, description=description
    )


def _retention(description: str) -> Any:
    return Field(
        default=None, gt=0, le=AMOUNT_MAX, decimal_places=2, description=description
    )


class ApproximateTaxes(_Model):
    """The approximate tax burden of Lei 12.741 (DPS `totTrib`).

    One shape: `simples_percent`; or the federal, state and municipal
    percentages; or the federal, state and municipal amounts.
    """

    simples_percent: Decimal | None = _percent(
        "pTotTribSN, 0 to 99.99. ME/EPP only.", SIMPLES_PERCENT_MAX
    )
    federal_percent: Decimal | None = _percent("pTotTribFed, 0 to 100.")
    state_percent: Decimal | None = _percent("pTotTribEst, 0 to 100.")
    municipal_percent: Decimal | None = _percent("pTotTribMun, 0 to 100.")
    federal_amount: Decimal | None = _amount("vTotTribFed in BRL.")
    state_amount: Decimal | None = _amount("vTotTribEst in BRL.")
    municipal_amount: Decimal | None = _amount("vTotTribMun in BRL.")


class IssSuspension(_Model):
    """`exigSusp`: the ISSQN's exigibility suspended by a decision."""

    type: Literal["judicial", "administrative"] = Field(description="tpSusp.")
    process_number: str = Field(pattern=r"^[0-9]{30}$", description="nProcesso.")


class IssMunicipalBenefit(_Model):
    """`BM`: a benefit the municipality registered in the national system."""

    id: str = Field(pattern=r"^[0-9]{14}$", description="nBM, 14 digits.")
    reduction_amount: Decimal | None = Field(
        default=None,
        ge=0,
        le=AMOUNT_MAX,
        decimal_places=2,
        description="vRedBCBM in BRL.",
    )
    reduction_percent: Decimal | None = Field(
        default=None,
        gt=0,
        le=PERCENT_MAX,
        decimal_places=2,
        description="pRedBCBM, above 0 and up to 100.",
    )


class IssDetails(_Model):
    """The ISSQN of the service (DPS `tribMun`)."""

    taxation: Literal["taxable", "immune", "export", "not_levied"] | None = Field(
        default=None,
        description="tribISSQN: taxable (the API's default), immune, export or not_levied.",
    )
    immunity_type: int | None = Field(
        default=None, ge=1, le=5, description="tpImunidade, with taxation=immune."
    )
    result_country_code: str | None = Field(
        default=None,
        pattern=r"^[A-Z]{2}$",
        description="cPaisResult, ISO alpha-2, with taxation=export.",
    )
    suspension: IssSuspension | None = Field(default=None, description="exigSusp.")
    rate: Decimal | None = Field(
        default=None,
        gt=0,
        le=ISS_RATE_MAX,
        decimal_places=2,
        description="pAliq in percent, above 0 and at most 5. Refused for an MEI.",
    )
    retention: Literal["none", "tomador", "intermediary"] | None = Field(
        default=None, description="tpRetISSQN."
    )
    municipal_benefit: IssMunicipalBenefit | None = Field(
        default=None, description="BM."
    )


class PisCofins(_Model):
    """`piscofins`: the PIS and COFINS of the service."""

    cst: PisCofinsCst = Field(description="The PIS/COFINS CST, two digits.")
    base: Decimal | None = _amount("vBCPisCofins in BRL.")
    pis_rate: Decimal | None = _percent("pAliqPis, 0 to 99.99.", SIMPLES_PERCENT_MAX)
    cofins_rate: Decimal | None = _percent(
        "pAliqCofins, 0 to 99.99.", SIMPLES_PERCENT_MAX
    )
    pis_amount: Decimal | None = _amount("vPis in BRL.")
    cofins_amount: Decimal | None = _amount("vCofins in BRL.")
    withholding_type: int | None = Field(
        default=None, ge=0, le=9, description="tpRetPisCofins, 0 to 9."
    )


class FederalTaxes(_Model):
    """The federal taxes of the service (DPS `tribFed`)."""

    pis_cofins: PisCofins | None = Field(default=None, description="piscofins.")
    social_security_withheld: Decimal | None = _retention("vRetCP in BRL.")
    irrf_withheld: Decimal | None = _retention("vRetIRRF in BRL.")
    social_contributions_withheld: Decimal | None = _retention(
        "vRetCSLL in BRL: the PIS, COFINS and CSLL withheld, summed."
    )


class ServiceAddress(_Model):
    """A Brazilian address of a construction, an event or a property."""

    zip_code: str = Field(pattern=r"^\d{8}$", description="CEP, eight digits.")
    street: str = Field(min_length=1, max_length=255, description="xLgr.")
    number: str = Field(min_length=1, max_length=60, description="nro.")
    complement: str | None = Field(
        default=None, min_length=1, max_length=156, description="xCpl."
    )
    neighborhood: str = Field(min_length=1, max_length=60, description="xBairro.")


class Construction(_Model):
    """The DPS `obra` group: a construction, by CNO or CIB or by address."""

    property_registration: str | None = Field(
        default=None, min_length=1, max_length=30, description="inscImobFisc."
    )
    work_id_type: Literal["cno", "cib"] | None = Field(
        default=None, description="What work_id is: cno (cObra) or cib (cCIB)."
    )
    work_id: str | None = Field(default=None, min_length=1, max_length=30)
    address: ServiceAddress | None = Field(default=None, description="end.")


class Event(_Model):
    """The DPS `atvEvento` group: an activity or event, by code or address."""

    name: str = Field(min_length=1, max_length=255, description="xNome.")
    start_date: date = Field(description="dtIni.")
    end_date: date = Field(description="dtFim.")
    event_id: str | None = Field(
        default=None, min_length=1, max_length=30, description="idAtvEvt."
    )
    address: ServiceAddress | None = Field(default=None, description="end.")


class References(_Model):
    """The DPS `infoCompl` references of the service."""

    order_number: str | None = Field(
        default=None, min_length=1, max_length=60, description="xPed."
    )
    order_items: list[Annotated[str, Field(min_length=1, max_length=60)]] | None = (
        Field(default=None, min_length=1, max_length=99, description="gItemPed.")
    )
    reference_document: str | None = Field(
        default=None, min_length=1, max_length=255, description="docRef."
    )
    technical_document: str | None = Field(
        default=None, min_length=1, max_length=40, description="idDocTec."
    )


class PersonAddress(_Model):
    """An address of a person: city_code and zip_code for one in Brazil,
    country_code, postal_code, city and state for one abroad."""

    street: str = Field(min_length=1, max_length=255, description="xLgr.")
    number: str = Field(min_length=1, max_length=60, description="nro.")
    complement: str | None = Field(
        default=None, min_length=1, max_length=156, description="xCpl."
    )
    neighborhood: str = Field(min_length=1, max_length=60, description="xBairro.")
    city_code: str | None = Field(
        default=None, pattern=r"^\d{7}$", description="endNac/cMun, IBGE code."
    )
    zip_code: str | None = Field(
        default=None, pattern=r"^\d{8}$", description="endNac/CEP."
    )
    country_code: str | None = Field(
        default=None,
        pattern=r"^[A-Z]{2}$",
        description="endExt/cPais, ISO alpha-2 other than BR.",
    )
    postal_code: str | None = Field(
        default=None, min_length=1, max_length=11, description="endExt/cEndPost."
    )
    city: str | None = Field(
        default=None, min_length=1, max_length=60, description="endExt/xCidade."
    )
    state: str | None = Field(
        default=None, min_length=1, max_length=60, description="endExt/xEstProvReg."
    )


class DeductionSupplier(_Model):
    """`fornec`: who issued the deducted document."""

    tax_id: str | None = Field(
        default=None, description="CPF or CNPJ of a supplier in Brazil."
    )
    foreign_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=40,
        description="NIF of a supplier abroad.",
    )
    name: str = Field(min_length=1, max_length=150, description="xNome.")
    address: PersonAddress = Field(description="fornec/end.")


class MunicipalNfse(_Model):
    """A municipal NFS-e outside the national repository (`NFSeMun`)."""

    city_code: str = Field(pattern=r"^\d{7}$", description="cMunNFSeMun.")
    number: str = Field(pattern=r"^\d{1,15}$", description="nNFSeMun.")
    verification_code: str = Field(
        pattern=r"^[A-Za-z0-9]{1,9}$", description="cVerifNFSeMun."
    )


class PaperInvoice(_Model):
    """A paper service invoice (`NFNFS`)."""

    number: str = Field(pattern=r"^\d{1,7}$", description="nNFS.")
    model: str = Field(pattern=r"^\d{1,15}$", description="modNFS.")
    series: str = Field(pattern=r"^[A-Za-z0-9]{1,15}$", description="serieNFS.")


class OtherFiscalDocument(_Model):
    """A fiscal document outside the national repository."""

    number: str = Field(min_length=1, max_length=255, description="nDocFisc.")
    city_code: str | None = Field(
        default=None, pattern=r"^\d{7}$", description="cMunDocFiscal."
    )
    description: str | None = Field(
        default=None, min_length=1, max_length=255, description="xDocFiscal."
    )


class OtherDocument(_Model):
    """A non-fiscal document."""

    number: str = Field(min_length=1, max_length=255, description="nDoc.")
    description: str | None = Field(
        default=None, min_length=1, max_length=255, description="xDoc."
    )


class DeductionDocument(_Model):
    """One document behind a deduction (`docDedRed` or `docAjusteBC`).

    Exactly one of `nfse_key`, `nfe_key`, `cte_key`, `municipal_nfse`,
    `paper_invoice`, `fiscal_document` and `other_document` identifies it.
    """

    type: DeductionType = Field(description="tpDedRed or tpAjusteBC.")
    description: str | None = Field(
        default=None, min_length=1, max_length=150, description="Types 99 and 199."
    )
    nfse_key: str | None = Field(default=None, pattern=NFSE_KEY_PATTERN)
    nfe_key: str | None = Field(default=None, pattern=NFE_KEY_PATTERN)
    cte_key: str | None = Field(default=None, pattern=NFE_KEY_PATTERN)
    municipal_nfse: MunicipalNfse | None = None
    paper_invoice: PaperInvoice | None = None
    fiscal_document: OtherFiscalDocument | None = None
    other_document: OtherDocument | None = None
    issue_date: date = Field(description="dtEmiDoc.")
    competence_date: date | None = Field(default=None, description="dtCompDoc.")
    total_amount: Decimal = Field(
        gt=0, le=AMOUNT_MAX, decimal_places=2, description="The document's value."
    )
    deducted_amount: Decimal = Field(
        gt=0, le=AMOUNT_MAX, decimal_places=2, description="The deducted value."
    )
    supplier: DeductionSupplier | None = Field(default=None, description="fornec.")


class Deductions(_Model):
    """The ISSQN base deduction or reduction (`vDedRed` or `vAjusteBC`)."""

    percent: Decimal | None = Field(
        default=None, gt=0, le=PERCENT_MAX, decimal_places=2, description="pDR."
    )
    amount: Decimal | None = Field(
        default=None, gt=0, le=AMOUNT_MAX, decimal_places=2, description="vDR."
    )
    documents: list[DeductionDocument] | None = Field(
        default=None, min_length=1, max_length=1000
    )


class Substitution(_Model):
    """`subst`: the authorized NFS-e this one replaces."""

    access_key: str = Field(pattern=NFSE_KEY_PATTERN, description="chSubstda.")
    reason_code: Literal["01", "02", "03", "04", "05", "99"] = Field(
        description="cMotivo."
    )
    reason: str | None = Field(
        default=None,
        min_length=15,
        max_length=255,
        description="xMotivo, required with reason_code 99.",
    )


class NfseIntermediary(_Model):
    """The DPS `interm` group, identified by exactly one of `tax_id`,
    `foreign_id` or `foreign_id_missing_reason`."""

    tax_id: str | None = Field(default=None, description="CNPJ or CPF.")
    foreign_id: str | None = Field(
        default=None, min_length=1, max_length=40, description="NIF."
    )
    foreign_id_missing_reason: Literal[1, 2] | None = Field(
        default=None, description="cNaoNIF: 1 exempt, 2 not required."
    )
    caepf: str | None = Field(default=None, pattern=r"^\d{14}$")
    municipal_registration: str | None = Field(
        default=None, pattern=r"^[A-Za-z0-9]{1,15}$", description="IM."
    )
    name: str = Field(min_length=1, max_length=300, description="xNome.")
    address: PersonAddress | None = Field(default=None, description="interm/end.")
    phone: str | None = Field(default=None, description="fone.")
    email: str | None = Field(default=None, description="email.")


class ForeignTrade(_Model):
    """The DPS `comExt` group: a service traded with someone abroad."""

    service_mode: Literal[1, 2, 3, 4] = Field(description="mdPrestacao.")
    relationship: Literal[0, 1, 2, 3, 4, 5, 6, 9] = Field(description="vincPrest.")
    currency_code: str = Field(pattern=r"^\d{3}$", description="tpMoeda.")
    foreign_amount: Decimal = Field(
        gt=0, le=AMOUNT_MAX, decimal_places=2, description="vServMoeda."
    )
    provider_support: int = Field(ge=1, le=8, description="mecAFComexP.")
    recipient_support: int = Field(ge=1, le=26, description="mecAFComexT.")
    temporary_goods: Literal[1, 2, 3] = Field(description="movTempBens.")
    import_declaration: str | None = Field(
        default=None, min_length=1, max_length=12, description="nDI."
    )
    export_registration: str | None = Field(
        default=None, min_length=1, max_length=12, description="nRE."
    )
    share_with_mdic: bool | None = Field(default=None, description="mdic.")


class NfseDetails(_Model):
    """The document-level fields of an NFS-e, beyond its lines.

    Sent as `nfse` on `issue()` and `validate()`. NFS-e only.
    """

    approximate_taxes: ApproximateTaxes | None = None
    competence_date: date | None = Field(default=None, description="dCompet.")
    service_city_code: str | None = Field(
        default=None, pattern=r"^\d{7}$", description="cLocPrestacao, IBGE code."
    )
    service_country_code: str | None = Field(
        default=None,
        pattern=r"^[A-Z]{2}$",
        description="cPaisPrestacao, ISO alpha-2, for a service performed abroad.",
    )
    iss: IssDetails | None = None
    federal: FederalTaxes | None = None
    deductions: Deductions | None = None
    substitution: Substitution | None = None
    construction: Construction | None = None
    event: Event | None = None
    references: References | None = None
    intermediary: NfseIntermediary | None = None
    foreign_trade: ForeignTrade | None = None


class IbsCbsGovernment(_Model):
    """`tpOper` and `tpEnteGov` of an NFS-e's IBS/CBS group."""

    operation_type: Literal["1", "2", "3", "4", "5"] | None = Field(
        default=None, description="tpOper."
    )
    entity_type: Literal["1", "2", "3", "4"] | None = Field(
        default=None, description="tpEnteGov."
    )


class IbsCbsRecipientAddress(_Model):
    """The `dest/end` address, in Brazil or abroad."""

    street: str = Field(min_length=1, max_length=255, description="xLgr.")
    number: str = Field(min_length=1, max_length=60, description="nro.")
    complement: str | None = Field(
        default=None, min_length=1, max_length=156, description="xCpl."
    )
    neighborhood: str = Field(min_length=1, max_length=60, description="xBairro.")
    city_code: str | None = Field(default=None, pattern=r"^\d{7}$")
    zip_code: str | None = Field(default=None, pattern=r"^\d{8}$")
    country_code: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    postal_code: str | None = Field(default=None, min_length=1, max_length=11)
    city: str | None = Field(default=None, min_length=1, max_length=60)
    region: str | None = Field(default=None, min_length=1, max_length=60)


class IbsCbsRecipient(_Model):
    """`dest`: who receives the service when it is not the tomador."""

    tax_id: str | None = Field(default=None, pattern=r"^\d{11}$|^[0-9A-Z]{12}\d{2}$")
    nif: str | None = Field(default=None, min_length=1, max_length=40)
    no_nif_reason: Literal["0", "1", "2"] | None = Field(
        default=None, description="cNaoNIF."
    )
    name: str = Field(min_length=1, max_length=150, description="xNome.")
    address: IbsCbsRecipientAddress | None = Field(default=None, description="end.")
    phone: str | None = Field(default=None, pattern=r"^\d{6,20}$")
    email: str | None = Field(
        default=None, max_length=80, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )


class RealEstateLease(_Model):
    """`gLocacao`: a lease, onerous assignment or rental of real estate."""

    co_ownership_percent: float = Field(ge=0, le=100, description="pCopropriedade.")
    total_amount: float = Field(ge=0, le=float(AMOUNT_MAX), description="vTotOper.")
    unconditional_discount: float | None = Field(
        default=None, ge=0, le=float(AMOUNT_MAX)
    )
    conditional_discount: float | None = Field(default=None, ge=0, le=float(AMOUNT_MAX))
    original_due_date: date | None = Field(default=None, description="dVencOrig.")


class RealEstateBaseAdjustment(_Model):
    """`gAjusteBCLocImoveis`: an amount inside the rent outside the base."""

    type: Literal["01", "02", "03", "04", "99"]
    description: str | None = Field(default=None, min_length=1, max_length=150)
    amount: float = Field(ge=0, le=float(AMOUNT_MAX))


class RealEstateUnit(_Model):
    """One property, identified by `cib` or `address`."""

    property_registration: str | None = Field(default=None, min_length=1, max_length=30)
    cib: str | None = Field(default=None, pattern=r"^[0-9A-Z]{8}$")
    address: ServiceAddress | None = None
    base_adjustments: list[RealEstateBaseAdjustment] | None = Field(
        default=None, min_length=1, max_length=1000
    )


class RealEstate(_Model):
    """`imovel`: an operation on real estate other than civil works."""

    city_code: str | None = Field(default=None, pattern=r"^\d{7}$")
    lease: RealEstateLease | None = None
    units: list[RealEstateUnit] | None = Field(
        default=None, min_length=1, max_length=99
    )


class MovableGood(_Model):
    """`bensMoveis`: a movable good the service leases."""

    ncm: str = Field(pattern=r"^\d{8}$")
    description: str = Field(min_length=1, max_length=150)
    quantity: int = Field(ge=1, le=999)


class IbsCbsRegularTaxation(_Model):
    """`gTribRegular`: the CST and cClassTrib under regular taxation."""

    cst: str = Field(pattern=r"^\d{3}$")
    classification: str = Field(pattern=r"^\d{6}$")


class IbsCbsDeferral(_Model):
    """`gDif`: the deferred share of each tax, in percent."""

    state_percent: float = Field(ge=0, le=100)
    city_percent: float = Field(ge=0, le=100)
    cbs_percent: float = Field(ge=0, le=100)
