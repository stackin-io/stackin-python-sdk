"""Tax module."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

_CONFIG = ConfigDict(populate_by_name=True)


_IpiNtCst = Literal[
    "01",
    "02",
    "03",
    "04",
    "05",
    "51",
    "52",
    "53",
    "54",
    "55",
]


_PisOutrCst = Literal[
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


_CofinsOutrCst = Literal[
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


class Icms00(BaseModel):
    """ICMS fully taxed."""

    model_config = _CONFIG

    orig: str
    cst: Literal["00"] = Field(
        default="00",
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    mod_bc: str = Field(
        validation_alias=AliasChoices("mod_bc", "modBC"),
        serialization_alias="modBC",
    )
    v_bc: str = Field(
        validation_alias=AliasChoices("v_bc", "vBC"),
        serialization_alias="vBC",
    )
    p_icms: str = Field(
        validation_alias=AliasChoices("p_icms", "pICMS"),
        serialization_alias="pICMS",
    )
    v_icms: str = Field(
        validation_alias=AliasChoices("v_icms", "vICMS"),
        serialization_alias="vICMS",
    )
    p_fcp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp", "pFCP"),
        serialization_alias="pFCP",
    )
    v_fcp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp", "vFCP"),
        serialization_alias="vFCP",
    )


class Icms02(BaseModel):
    """ICMS monofasico, taxed by unit."""

    model_config = _CONFIG

    orig: str
    cst: Literal["02"] = Field(
        default="02",
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    q_bc_mono: str | None = Field(
        default=None,
        validation_alias=AliasChoices("q_bc_mono", "qBCMono"),
        serialization_alias="qBCMono",
    )
    ad_rem_icms: str = Field(
        validation_alias=AliasChoices("ad_rem_icms", "adRemICMS"),
        serialization_alias="adRemICMS",
    )
    v_icms_mono: str = Field(
        validation_alias=AliasChoices("v_icms_mono", "vICMSMono"),
        serialization_alias="vICMSMono",
    )


class Icms10(BaseModel):
    """ICMS taxed with substitution."""

    model_config = _CONFIG

    orig: str
    cst: Literal["10"] = Field(
        default="10",
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    mod_bc: str = Field(
        validation_alias=AliasChoices("mod_bc", "modBC"),
        serialization_alias="modBC",
    )
    v_bc: str = Field(
        validation_alias=AliasChoices("v_bc", "vBC"),
        serialization_alias="vBC",
    )
    p_icms: str = Field(
        validation_alias=AliasChoices("p_icms", "pICMS"),
        serialization_alias="pICMS",
    )
    v_icms: str = Field(
        validation_alias=AliasChoices("v_icms", "vICMS"),
        serialization_alias="vICMS",
    )
    v_bc_fcp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_fcp", "vBCFCP"),
        serialization_alias="vBCFCP",
    )
    p_fcp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp", "pFCP"),
        serialization_alias="pFCP",
    )
    v_fcp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp", "vFCP"),
        serialization_alias="vFCP",
    )
    mod_bc_st: str = Field(
        validation_alias=AliasChoices("mod_bc_st", "modBCST"),
        serialization_alias="modBCST",
    )
    p_mva_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_mva_st", "pMVAST"),
        serialization_alias="pMVAST",
    )
    p_red_bc_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_red_bc_st", "pRedBCST"),
        serialization_alias="pRedBCST",
    )
    v_bc_st: str = Field(
        validation_alias=AliasChoices("v_bc_st", "vBCST"),
        serialization_alias="vBCST",
    )
    p_icms_st: str = Field(
        validation_alias=AliasChoices("p_icms_st", "pICMSST"),
        serialization_alias="pICMSST",
    )
    v_icms_st: str = Field(
        validation_alias=AliasChoices("v_icms_st", "vICMSST"),
        serialization_alias="vICMSST",
    )
    v_bc_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_fcp_st", "vBCFCPST"),
        serialization_alias="vBCFCPST",
    )
    p_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp_st", "pFCPST"),
        serialization_alias="pFCPST",
    )
    v_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp_st", "vFCPST"),
        serialization_alias="vFCPST",
    )
    v_icms_st_deson: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_st_deson", "vICMSSTDeson"),
        serialization_alias="vICMSSTDeson",
    )
    mot_des_icms_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("mot_des_icms_st", "motDesICMSST"),
        serialization_alias="motDesICMSST",
    )


class Icms15(BaseModel):
    """ICMS monofasico with retention."""

    model_config = _CONFIG

    orig: str
    cst: Literal["15"] = Field(
        default="15",
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    q_bc_mono: str | None = Field(
        default=None,
        validation_alias=AliasChoices("q_bc_mono", "qBCMono"),
        serialization_alias="qBCMono",
    )
    ad_rem_icms: str = Field(
        validation_alias=AliasChoices("ad_rem_icms", "adRemICMS"),
        serialization_alias="adRemICMS",
    )
    v_icms_mono: str = Field(
        validation_alias=AliasChoices("v_icms_mono", "vICMSMono"),
        serialization_alias="vICMSMono",
    )
    q_bc_mono_reten: str | None = Field(
        default=None,
        validation_alias=AliasChoices("q_bc_mono_reten", "qBCMonoReten"),
        serialization_alias="qBCMonoReten",
    )
    ad_rem_icms_reten: str = Field(
        validation_alias=AliasChoices("ad_rem_icms_reten", "adRemICMSReten"),
        serialization_alias="adRemICMSReten",
    )
    v_icms_mono_reten: str = Field(
        validation_alias=AliasChoices("v_icms_mono_reten", "vICMSMonoReten"),
        serialization_alias="vICMSMonoReten",
    )
    p_red_ad_rem: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_red_ad_rem", "pRedAdRem"),
        serialization_alias="pRedAdRem",
    )
    mot_red_ad_rem: str | None = Field(
        default=None,
        validation_alias=AliasChoices("mot_red_ad_rem", "motRedAdRem"),
        serialization_alias="motRedAdRem",
    )


class Icms20(BaseModel):
    """ICMS with a reduced base."""

    model_config = _CONFIG

    orig: str
    cst: Literal["20"] = Field(
        default="20",
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    mod_bc: str = Field(
        validation_alias=AliasChoices("mod_bc", "modBC"),
        serialization_alias="modBC",
    )
    p_red_bc: str = Field(
        validation_alias=AliasChoices("p_red_bc", "pRedBC"),
        serialization_alias="pRedBC",
    )
    v_bc: str = Field(
        validation_alias=AliasChoices("v_bc", "vBC"),
        serialization_alias="vBC",
    )
    p_icms: str = Field(
        validation_alias=AliasChoices("p_icms", "pICMS"),
        serialization_alias="pICMS",
    )
    v_icms: str = Field(
        validation_alias=AliasChoices("v_icms", "vICMS"),
        serialization_alias="vICMS",
    )
    v_bc_fcp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_fcp", "vBCFCP"),
        serialization_alias="vBCFCP",
    )
    p_fcp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp", "pFCP"),
        serialization_alias="pFCP",
    )
    v_fcp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp", "vFCP"),
        serialization_alias="vFCP",
    )
    v_icms_deson: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_deson", "vICMSDeson"),
        serialization_alias="vICMSDeson",
    )
    mot_des_icms: str | None = Field(
        default=None,
        validation_alias=AliasChoices("mot_des_icms", "motDesICMS"),
        serialization_alias="motDesICMS",
    )
    ind_deduz_deson: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ind_deduz_deson", "indDeduzDeson"),
        serialization_alias="indDeduzDeson",
    )


class Icms30(BaseModel):
    """ICMS exempt with substitution."""

    model_config = _CONFIG

    orig: str
    cst: Literal["30"] = Field(
        default="30",
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    mod_bc_st: str = Field(
        validation_alias=AliasChoices("mod_bc_st", "modBCST"),
        serialization_alias="modBCST",
    )
    p_mva_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_mva_st", "pMVAST"),
        serialization_alias="pMVAST",
    )
    p_red_bc_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_red_bc_st", "pRedBCST"),
        serialization_alias="pRedBCST",
    )
    v_bc_st: str = Field(
        validation_alias=AliasChoices("v_bc_st", "vBCST"),
        serialization_alias="vBCST",
    )
    p_icms_st: str = Field(
        validation_alias=AliasChoices("p_icms_st", "pICMSST"),
        serialization_alias="pICMSST",
    )
    v_icms_st: str = Field(
        validation_alias=AliasChoices("v_icms_st", "vICMSST"),
        serialization_alias="vICMSST",
    )
    v_bc_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_fcp_st", "vBCFCPST"),
        serialization_alias="vBCFCPST",
    )
    p_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp_st", "pFCPST"),
        serialization_alias="pFCPST",
    )
    v_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp_st", "vFCPST"),
        serialization_alias="vFCPST",
    )
    v_icms_deson: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_deson", "vICMSDeson"),
        serialization_alias="vICMSDeson",
    )
    mot_des_icms: str | None = Field(
        default=None,
        validation_alias=AliasChoices("mot_des_icms", "motDesICMS"),
        serialization_alias="motDesICMS",
    )
    ind_deduz_deson: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ind_deduz_deson", "indDeduzDeson"),
        serialization_alias="indDeduzDeson",
    )


class Icms40(BaseModel):
    """ICMS exempt or not taxed."""

    model_config = _CONFIG

    orig: str
    cst: Literal["40", "41", "50"] = Field(
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    v_icms_deson: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_deson", "vICMSDeson"),
        serialization_alias="vICMSDeson",
    )
    mot_des_icms: str | None = Field(
        default=None,
        validation_alias=AliasChoices("mot_des_icms", "motDesICMS"),
        serialization_alias="motDesICMS",
    )
    ind_deduz_deson: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ind_deduz_deson", "indDeduzDeson"),
        serialization_alias="indDeduzDeson",
    )


class Icms51(BaseModel):
    """ICMS deferred."""

    model_config = _CONFIG

    orig: str
    cst: Literal["51"] = Field(
        default="51",
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    mod_bc: str | None = Field(
        default=None,
        validation_alias=AliasChoices("mod_bc", "modBC"),
        serialization_alias="modBC",
    )
    p_red_bc: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_red_bc", "pRedBC"),
        serialization_alias="pRedBC",
    )
    c_benef_rbc: str | None = Field(
        default=None,
        validation_alias=AliasChoices("c_benef_rbc", "cBenefRBC"),
        serialization_alias="cBenefRBC",
    )
    v_bc: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc", "vBC"),
        serialization_alias="vBC",
    )
    p_icms: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_icms", "pICMS"),
        serialization_alias="pICMS",
    )
    v_icms_op: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_op", "vICMSOp"),
        serialization_alias="vICMSOp",
    )
    p_dif: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_dif", "pDif"),
        serialization_alias="pDif",
    )
    v_icms_dif: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_dif", "vICMSDif"),
        serialization_alias="vICMSDif",
    )
    v_icms: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms", "vICMS"),
        serialization_alias="vICMS",
    )
    v_bc_fcp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_fcp", "vBCFCP"),
        serialization_alias="vBCFCP",
    )
    p_fcp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp", "pFCP"),
        serialization_alias="pFCP",
    )
    v_fcp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp", "vFCP"),
        serialization_alias="vFCP",
    )
    p_fcp_dif: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp_dif", "pFCPDif"),
        serialization_alias="pFCPDif",
    )
    v_fcp_dif: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp_dif", "vFCPDif"),
        serialization_alias="vFCPDif",
    )
    v_fcp_efet: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp_efet", "vFCPEfet"),
        serialization_alias="vFCPEfet",
    )


class Icms53(BaseModel):
    """ICMS monofasico deferred."""

    model_config = _CONFIG

    orig: str
    cst: Literal["53"] = Field(
        default="53",
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    q_bc_mono: str | None = Field(
        default=None,
        validation_alias=AliasChoices("q_bc_mono", "qBCMono"),
        serialization_alias="qBCMono",
    )
    ad_rem_icms: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ad_rem_icms", "adRemICMS"),
        serialization_alias="adRemICMS",
    )
    v_icms_mono_op: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_mono_op", "vICMSMonoOp"),
        serialization_alias="vICMSMonoOp",
    )
    p_dif: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_dif", "pDif"),
        serialization_alias="pDif",
    )
    v_icms_mono_dif: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_mono_dif", "vICMSMonoDif"),
        serialization_alias="vICMSMonoDif",
    )
    v_icms_mono: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_mono", "vICMSMono"),
        serialization_alias="vICMSMono",
    )
    q_bc_mono_dif: str | None = Field(
        default=None,
        validation_alias=AliasChoices("q_bc_mono_dif", "qBCMonoDif"),
        serialization_alias="qBCMonoDif",
    )
    ad_rem_icms_dif: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ad_rem_icms_dif", "adRemICMSDif"),
        serialization_alias="adRemICMSDif",
    )


class Icms60(BaseModel):
    """ICMS already charged by an earlier substitution."""

    model_config = _CONFIG

    orig: str
    cst: Literal["60"] = Field(
        default="60",
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    v_bc_st_ret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_st_ret", "vBCSTRet"),
        serialization_alias="vBCSTRet",
    )
    p_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_st", "pST"),
        serialization_alias="pST",
    )
    v_icms_substituto: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_substituto", "vICMSSubstituto"),
        serialization_alias="vICMSSubstituto",
    )
    v_icms_st_ret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_st_ret", "vICMSSTRet"),
        serialization_alias="vICMSSTRet",
    )
    v_bc_fcp_st_ret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_fcp_st_ret", "vBCFCPSTRet"),
        serialization_alias="vBCFCPSTRet",
    )
    p_fcp_st_ret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp_st_ret", "pFCPSTRet"),
        serialization_alias="pFCPSTRet",
    )
    v_fcp_st_ret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp_st_ret", "vFCPSTRet"),
        serialization_alias="vFCPSTRet",
    )
    p_red_bc_efet: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_red_bc_efet", "pRedBCEfet"),
        serialization_alias="pRedBCEfet",
    )
    v_bc_efet: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_efet", "vBCEfet"),
        serialization_alias="vBCEfet",
    )
    p_icms_efet: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_icms_efet", "pICMSEfet"),
        serialization_alias="pICMSEfet",
    )
    v_icms_efet: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_efet", "vICMSEfet"),
        serialization_alias="vICMSEfet",
    )


class Icms61(BaseModel):
    """ICMS monofasico already charged earlier."""

    model_config = _CONFIG

    orig: str
    cst: Literal["61"] = Field(
        default="61",
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    q_bc_mono_ret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("q_bc_mono_ret", "qBCMonoRet"),
        serialization_alias="qBCMonoRet",
    )
    ad_rem_icms_ret: str = Field(
        validation_alias=AliasChoices("ad_rem_icms_ret", "adRemICMSRet"),
        serialization_alias="adRemICMSRet",
    )
    v_icms_mono_ret: str = Field(
        validation_alias=AliasChoices("v_icms_mono_ret", "vICMSMonoRet"),
        serialization_alias="vICMSMonoRet",
    )


class Icms70(BaseModel):
    """ICMS with a reduced base and substitution."""

    model_config = _CONFIG

    orig: str
    cst: Literal["70"] = Field(
        default="70",
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    mod_bc: str = Field(
        validation_alias=AliasChoices("mod_bc", "modBC"),
        serialization_alias="modBC",
    )
    p_red_bc: str = Field(
        validation_alias=AliasChoices("p_red_bc", "pRedBC"),
        serialization_alias="pRedBC",
    )
    v_bc: str = Field(
        validation_alias=AliasChoices("v_bc", "vBC"),
        serialization_alias="vBC",
    )
    p_icms: str = Field(
        validation_alias=AliasChoices("p_icms", "pICMS"),
        serialization_alias="pICMS",
    )
    v_icms: str = Field(
        validation_alias=AliasChoices("v_icms", "vICMS"),
        serialization_alias="vICMS",
    )
    v_bc_fcp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_fcp", "vBCFCP"),
        serialization_alias="vBCFCP",
    )
    p_fcp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp", "pFCP"),
        serialization_alias="pFCP",
    )
    v_fcp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp", "vFCP"),
        serialization_alias="vFCP",
    )
    mod_bc_st: str = Field(
        validation_alias=AliasChoices("mod_bc_st", "modBCST"),
        serialization_alias="modBCST",
    )
    p_mva_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_mva_st", "pMVAST"),
        serialization_alias="pMVAST",
    )
    p_red_bc_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_red_bc_st", "pRedBCST"),
        serialization_alias="pRedBCST",
    )
    v_bc_st: str = Field(
        validation_alias=AliasChoices("v_bc_st", "vBCST"),
        serialization_alias="vBCST",
    )
    p_icms_st: str = Field(
        validation_alias=AliasChoices("p_icms_st", "pICMSST"),
        serialization_alias="pICMSST",
    )
    v_icms_st: str = Field(
        validation_alias=AliasChoices("v_icms_st", "vICMSST"),
        serialization_alias="vICMSST",
    )
    v_bc_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_fcp_st", "vBCFCPST"),
        serialization_alias="vBCFCPST",
    )
    p_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp_st", "pFCPST"),
        serialization_alias="pFCPST",
    )
    v_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp_st", "vFCPST"),
        serialization_alias="vFCPST",
    )
    v_icms_deson: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_deson", "vICMSDeson"),
        serialization_alias="vICMSDeson",
    )
    mot_des_icms: str | None = Field(
        default=None,
        validation_alias=AliasChoices("mot_des_icms", "motDesICMS"),
        serialization_alias="motDesICMS",
    )
    ind_deduz_deson: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ind_deduz_deson", "indDeduzDeson"),
        serialization_alias="indDeduzDeson",
    )
    v_icms_st_deson: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_st_deson", "vICMSSTDeson"),
        serialization_alias="vICMSSTDeson",
    )
    mot_des_icms_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("mot_des_icms_st", "motDesICMSST"),
        serialization_alias="motDesICMSST",
    )


class Icms90(BaseModel):
    """ICMS, other cases."""

    model_config = _CONFIG

    orig: str
    cst: Literal["90"] = Field(
        default="90",
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    mod_bc: str | None = Field(
        default=None,
        validation_alias=AliasChoices("mod_bc", "modBC"),
        serialization_alias="modBC",
    )
    v_bc: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc", "vBC"),
        serialization_alias="vBC",
    )
    p_red_bc: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_red_bc", "pRedBC"),
        serialization_alias="pRedBC",
    )
    c_benef_rbc: str | None = Field(
        default=None,
        validation_alias=AliasChoices("c_benef_rbc", "cBenefRBC"),
        serialization_alias="cBenefRBC",
    )
    p_icms: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_icms", "pICMS"),
        serialization_alias="pICMS",
    )
    v_icms_op: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_op", "vICMSOp"),
        serialization_alias="vICMSOp",
    )
    p_dif: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_dif", "pDif"),
        serialization_alias="pDif",
    )
    v_icms_dif: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_dif", "vICMSDif"),
        serialization_alias="vICMSDif",
    )
    v_icms: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms", "vICMS"),
        serialization_alias="vICMS",
    )
    v_bc_fcp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_fcp", "vBCFCP"),
        serialization_alias="vBCFCP",
    )
    p_fcp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp", "pFCP"),
        serialization_alias="pFCP",
    )
    v_fcp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp", "vFCP"),
        serialization_alias="vFCP",
    )
    p_fcp_dif: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp_dif", "pFCPDif"),
        serialization_alias="pFCPDif",
    )
    v_fcp_dif: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp_dif", "vFCPDif"),
        serialization_alias="vFCPDif",
    )
    v_fcp_efet: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp_efet", "vFCPEfet"),
        serialization_alias="vFCPEfet",
    )
    mod_bc_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("mod_bc_st", "modBCST"),
        serialization_alias="modBCST",
    )
    p_mva_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_mva_st", "pMVAST"),
        serialization_alias="pMVAST",
    )
    p_red_bc_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_red_bc_st", "pRedBCST"),
        serialization_alias="pRedBCST",
    )
    v_bc_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_st", "vBCST"),
        serialization_alias="vBCST",
    )
    p_icms_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_icms_st", "pICMSST"),
        serialization_alias="pICMSST",
    )
    v_icms_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_st", "vICMSST"),
        serialization_alias="vICMSST",
    )
    v_bc_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_fcp_st", "vBCFCPST"),
        serialization_alias="vBCFCPST",
    )
    p_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp_st", "pFCPST"),
        serialization_alias="pFCPST",
    )
    v_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp_st", "vFCPST"),
        serialization_alias="vFCPST",
    )
    v_icms_deson: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_deson", "vICMSDeson"),
        serialization_alias="vICMSDeson",
    )
    mot_des_icms: str | None = Field(
        default=None,
        validation_alias=AliasChoices("mot_des_icms", "motDesICMS"),
        serialization_alias="motDesICMS",
    )
    ind_deduz_deson: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ind_deduz_deson", "indDeduzDeson"),
        serialization_alias="indDeduzDeson",
    )
    v_icms_st_deson: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_st_deson", "vICMSSTDeson"),
        serialization_alias="vICMSSTDeson",
    )
    mot_des_icms_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("mot_des_icms_st", "motDesICMSST"),
        serialization_alias="motDesICMSST",
    )


class IcmsPart(BaseModel):
    """ICMS split between the origin and destination states."""

    model_config = _CONFIG

    orig: str
    cst: Literal["10", "20", "90"] = Field(
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    mod_bc: str = Field(
        validation_alias=AliasChoices("mod_bc", "modBC"),
        serialization_alias="modBC",
    )
    v_bc: str = Field(
        validation_alias=AliasChoices("v_bc", "vBC"),
        serialization_alias="vBC",
    )
    p_red_bc: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_red_bc", "pRedBC"),
        serialization_alias="pRedBC",
    )
    p_icms: str = Field(
        validation_alias=AliasChoices("p_icms", "pICMS"),
        serialization_alias="pICMS",
    )
    v_icms: str = Field(
        validation_alias=AliasChoices("v_icms", "vICMS"),
        serialization_alias="vICMS",
    )
    mod_bc_st: str = Field(
        validation_alias=AliasChoices("mod_bc_st", "modBCST"),
        serialization_alias="modBCST",
    )
    p_mva_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_mva_st", "pMVAST"),
        serialization_alias="pMVAST",
    )
    p_red_bc_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_red_bc_st", "pRedBCST"),
        serialization_alias="pRedBCST",
    )
    v_bc_st: str = Field(
        validation_alias=AliasChoices("v_bc_st", "vBCST"),
        serialization_alias="vBCST",
    )
    p_icms_st: str = Field(
        validation_alias=AliasChoices("p_icms_st", "pICMSST"),
        serialization_alias="pICMSST",
    )
    v_icms_st: str = Field(
        validation_alias=AliasChoices("v_icms_st", "vICMSST"),
        serialization_alias="vICMSST",
    )
    v_bc_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_fcp_st", "vBCFCPST"),
        serialization_alias="vBCFCPST",
    )
    p_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp_st", "pFCPST"),
        serialization_alias="pFCPST",
    )
    v_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp_st", "vFCPST"),
        serialization_alias="vFCPST",
    )
    p_bc_op: str = Field(
        validation_alias=AliasChoices("p_bc_op", "pBCOp"),
        serialization_alias="pBCOp",
    )
    uf_st: str = Field(
        validation_alias=AliasChoices("uf_st", "UFST"),
        serialization_alias="UFST",
    )
    v_icms_deson: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_deson", "vICMSDeson"),
        serialization_alias="vICMSDeson",
    )
    mot_des_icms: str | None = Field(
        default=None,
        validation_alias=AliasChoices("mot_des_icms", "motDesICMS"),
        serialization_alias="motDesICMS",
    )
    ind_deduz_deson: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ind_deduz_deson", "indDeduzDeson"),
        serialization_alias="indDeduzDeson",
    )


class IcmsSt(BaseModel):
    """ICMS charged earlier, for the substituted taxpayer."""

    model_config = _CONFIG

    orig: str
    cst: Literal["41", "60"] = Field(
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    v_bc_st_ret: str = Field(
        validation_alias=AliasChoices("v_bc_st_ret", "vBCSTRet"),
        serialization_alias="vBCSTRet",
    )
    p_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_st", "pST"),
        serialization_alias="pST",
    )
    v_icms_substituto: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_substituto", "vICMSSubstituto"),
        serialization_alias="vICMSSubstituto",
    )
    v_icms_st_ret: str = Field(
        validation_alias=AliasChoices("v_icms_st_ret", "vICMSSTRet"),
        serialization_alias="vICMSSTRet",
    )
    v_bc_fcp_st_ret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_fcp_st_ret", "vBCFCPSTRet"),
        serialization_alias="vBCFCPSTRet",
    )
    p_fcp_st_ret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp_st_ret", "pFCPSTRet"),
        serialization_alias="pFCPSTRet",
    )
    v_fcp_st_ret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp_st_ret", "vFCPSTRet"),
        serialization_alias="vFCPSTRet",
    )
    v_bc_st_dest: str = Field(
        validation_alias=AliasChoices("v_bc_st_dest", "vBCSTDest"),
        serialization_alias="vBCSTDest",
    )
    v_icms_st_dest: str = Field(
        validation_alias=AliasChoices("v_icms_st_dest", "vICMSSTDest"),
        serialization_alias="vICMSSTDest",
    )
    p_red_bc_efet: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_red_bc_efet", "pRedBCEfet"),
        serialization_alias="pRedBCEfet",
    )
    v_bc_efet: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_efet", "vBCEfet"),
        serialization_alias="vBCEfet",
    )
    p_icms_efet: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_icms_efet", "pICMSEfet"),
        serialization_alias="pICMSEfet",
    )
    v_icms_efet: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_efet", "vICMSEfet"),
        serialization_alias="vICMSEfet",
    )


class IcmsSn101(BaseModel):
    """Simples Nacional ICMS with a credit."""

    model_config = _CONFIG

    orig: str
    csosn: Literal["101"] = Field(
        default="101",
        validation_alias=AliasChoices("csosn", "CSOSN"),
        serialization_alias="CSOSN",
    )
    p_cred_sn: str = Field(
        validation_alias=AliasChoices("p_cred_sn", "pCredSN"),
        serialization_alias="pCredSN",
    )
    v_cred_icms_sn: str = Field(
        validation_alias=AliasChoices("v_cred_icms_sn", "vCredICMSSN"),
        serialization_alias="vCredICMSSN",
    )


class IcmsSn102(BaseModel):
    """Simples Nacional ICMS without a credit."""

    model_config = _CONFIG

    orig: str | None = None
    csosn: Literal["102", "103", "300", "400"] = Field(
        validation_alias=AliasChoices("csosn", "CSOSN"),
        serialization_alias="CSOSN",
    )


class IcmsSn201(BaseModel):
    """Simples Nacional ICMS with a credit and substitution."""

    model_config = _CONFIG

    orig: str
    csosn: Literal["201"] = Field(
        default="201",
        validation_alias=AliasChoices("csosn", "CSOSN"),
        serialization_alias="CSOSN",
    )
    mod_bc_st: str = Field(
        validation_alias=AliasChoices("mod_bc_st", "modBCST"),
        serialization_alias="modBCST",
    )
    p_mva_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_mva_st", "pMVAST"),
        serialization_alias="pMVAST",
    )
    p_red_bc_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_red_bc_st", "pRedBCST"),
        serialization_alias="pRedBCST",
    )
    v_bc_st: str = Field(
        validation_alias=AliasChoices("v_bc_st", "vBCST"),
        serialization_alias="vBCST",
    )
    p_icms_st: str = Field(
        validation_alias=AliasChoices("p_icms_st", "pICMSST"),
        serialization_alias="pICMSST",
    )
    v_icms_st: str = Field(
        validation_alias=AliasChoices("v_icms_st", "vICMSST"),
        serialization_alias="vICMSST",
    )
    v_bc_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_fcp_st", "vBCFCPST"),
        serialization_alias="vBCFCPST",
    )
    p_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp_st", "pFCPST"),
        serialization_alias="pFCPST",
    )
    v_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp_st", "vFCPST"),
        serialization_alias="vFCPST",
    )
    p_cred_sn: str = Field(
        validation_alias=AliasChoices("p_cred_sn", "pCredSN"),
        serialization_alias="pCredSN",
    )
    v_cred_icms_sn: str = Field(
        validation_alias=AliasChoices("v_cred_icms_sn", "vCredICMSSN"),
        serialization_alias="vCredICMSSN",
    )


class IcmsSn202(BaseModel):
    """Simples Nacional ICMS without a credit, with substitution."""

    model_config = _CONFIG

    orig: str
    csosn: Literal["202", "203"] = Field(
        validation_alias=AliasChoices("csosn", "CSOSN"),
        serialization_alias="CSOSN",
    )
    mod_bc_st: str = Field(
        validation_alias=AliasChoices("mod_bc_st", "modBCST"),
        serialization_alias="modBCST",
    )
    p_mva_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_mva_st", "pMVAST"),
        serialization_alias="pMVAST",
    )
    p_red_bc_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_red_bc_st", "pRedBCST"),
        serialization_alias="pRedBCST",
    )
    v_bc_st: str = Field(
        validation_alias=AliasChoices("v_bc_st", "vBCST"),
        serialization_alias="vBCST",
    )
    p_icms_st: str = Field(
        validation_alias=AliasChoices("p_icms_st", "pICMSST"),
        serialization_alias="pICMSST",
    )
    v_icms_st: str = Field(
        validation_alias=AliasChoices("v_icms_st", "vICMSST"),
        serialization_alias="vICMSST",
    )
    v_bc_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_fcp_st", "vBCFCPST"),
        serialization_alias="vBCFCPST",
    )
    p_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp_st", "pFCPST"),
        serialization_alias="pFCPST",
    )
    v_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp_st", "vFCPST"),
        serialization_alias="vFCPST",
    )


class IcmsSn500(BaseModel):
    """Simples Nacional ICMS already charged by substitution."""

    model_config = _CONFIG

    orig: str
    csosn: Literal["500"] = Field(
        default="500",
        validation_alias=AliasChoices("csosn", "CSOSN"),
        serialization_alias="CSOSN",
    )
    v_bc_st_ret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_st_ret", "vBCSTRet"),
        serialization_alias="vBCSTRet",
    )
    p_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_st", "pST"),
        serialization_alias="pST",
    )
    v_icms_substituto: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_substituto", "vICMSSubstituto"),
        serialization_alias="vICMSSubstituto",
    )
    v_icms_st_ret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_st_ret", "vICMSSTRet"),
        serialization_alias="vICMSSTRet",
    )
    v_bc_fcp_st_ret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_fcp_st_ret", "vBCFCPSTRet"),
        serialization_alias="vBCFCPSTRet",
    )
    p_fcp_st_ret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp_st_ret", "pFCPSTRet"),
        serialization_alias="pFCPSTRet",
    )
    v_fcp_st_ret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp_st_ret", "vFCPSTRet"),
        serialization_alias="vFCPSTRet",
    )
    p_red_bc_efet: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_red_bc_efet", "pRedBCEfet"),
        serialization_alias="pRedBCEfet",
    )
    v_bc_efet: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_efet", "vBCEfet"),
        serialization_alias="vBCEfet",
    )
    p_icms_efet: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_icms_efet", "pICMSEfet"),
        serialization_alias="pICMSEfet",
    )
    v_icms_efet: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_efet", "vICMSEfet"),
        serialization_alias="vICMSEfet",
    )


class IcmsSn900(BaseModel):
    """Simples Nacional ICMS, other cases."""

    model_config = _CONFIG

    orig: str | None = None
    csosn: Literal["900"] = Field(
        default="900",
        validation_alias=AliasChoices("csosn", "CSOSN"),
        serialization_alias="CSOSN",
    )
    mod_bc: str | None = Field(
        default=None,
        validation_alias=AliasChoices("mod_bc", "modBC"),
        serialization_alias="modBC",
    )
    v_bc: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc", "vBC"),
        serialization_alias="vBC",
    )
    p_red_bc: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_red_bc", "pRedBC"),
        serialization_alias="pRedBC",
    )
    p_icms: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_icms", "pICMS"),
        serialization_alias="pICMS",
    )
    v_icms: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms", "vICMS"),
        serialization_alias="vICMS",
    )
    mod_bc_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("mod_bc_st", "modBCST"),
        serialization_alias="modBCST",
    )
    p_mva_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_mva_st", "pMVAST"),
        serialization_alias="pMVAST",
    )
    p_red_bc_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_red_bc_st", "pRedBCST"),
        serialization_alias="pRedBCST",
    )
    v_bc_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_st", "vBCST"),
        serialization_alias="vBCST",
    )
    p_icms_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_icms_st", "pICMSST"),
        serialization_alias="pICMSST",
    )
    v_icms_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_icms_st", "vICMSST"),
        serialization_alias="vICMSST",
    )
    v_bc_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_fcp_st", "vBCFCPST"),
        serialization_alias="vBCFCPST",
    )
    p_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp_st", "pFCPST"),
        serialization_alias="pFCPST",
    )
    v_fcp_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp_st", "vFCPST"),
        serialization_alias="vFCPST",
    )
    p_cred_sn: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_cred_sn", "pCredSN"),
        serialization_alias="pCredSN",
    )
    v_cred_icms_sn: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_cred_icms_sn", "vCredICMSSN"),
        serialization_alias="vCredICMSSN",
    )


class IpiTrib(BaseModel):
    """IPI taxed by rate or by quantity."""

    model_config = _CONFIG

    cst: Literal["00", "49", "50", "99"] = Field(
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    v_bc: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc", "vBC"),
        serialization_alias="vBC",
    )
    p_ipi: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_ipi", "pIPI"),
        serialization_alias="pIPI",
    )
    q_unid: str | None = Field(
        default=None,
        validation_alias=AliasChoices("q_unid", "qUnid"),
        serialization_alias="qUnid",
    )
    v_unid: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_unid", "vUnid"),
        serialization_alias="vUnid",
    )
    v_ipi: str = Field(
        validation_alias=AliasChoices("v_ipi", "vIPI"),
        serialization_alias="vIPI",
    )


class IpiNt(BaseModel):
    """IPI not taxed."""

    model_config = _CONFIG

    cst: _IpiNtCst = Field(
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )


class PisAliq(BaseModel):
    """PIS taxed by rate."""

    model_config = _CONFIG

    cst: Literal["01", "02"] = Field(
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    v_bc: str = Field(
        validation_alias=AliasChoices("v_bc", "vBC"),
        serialization_alias="vBC",
    )
    p_pis: str = Field(
        validation_alias=AliasChoices("p_pis", "pPIS"),
        serialization_alias="pPIS",
    )
    v_pis: str = Field(
        validation_alias=AliasChoices("v_pis", "vPIS"),
        serialization_alias="vPIS",
    )


class PisQtde(BaseModel):
    """PIS taxed by quantity."""

    model_config = _CONFIG

    cst: Literal["03"] = Field(
        default="03",
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    q_bc_prod: str = Field(
        validation_alias=AliasChoices("q_bc_prod", "qBCProd"),
        serialization_alias="qBCProd",
    )
    v_aliq_prod: str = Field(
        validation_alias=AliasChoices("v_aliq_prod", "vAliqProd"),
        serialization_alias="vAliqProd",
    )
    v_pis: str = Field(
        validation_alias=AliasChoices("v_pis", "vPIS"),
        serialization_alias="vPIS",
    )


class PisNt(BaseModel):
    """PIS not taxed."""

    model_config = _CONFIG

    cst: Literal["04", "05", "06", "07", "08", "09"] = Field(
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )


class PisOutr(BaseModel):
    """PIS taxed some other way."""

    model_config = _CONFIG

    cst: _PisOutrCst = Field(
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    v_bc: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc", "vBC"),
        serialization_alias="vBC",
    )
    p_pis: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_pis", "pPIS"),
        serialization_alias="pPIS",
    )
    q_bc_prod: str | None = Field(
        default=None,
        validation_alias=AliasChoices("q_bc_prod", "qBCProd"),
        serialization_alias="qBCProd",
    )
    v_aliq_prod: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_aliq_prod", "vAliqProd"),
        serialization_alias="vAliqProd",
    )
    v_pis: str = Field(
        validation_alias=AliasChoices("v_pis", "vPIS"),
        serialization_alias="vPIS",
    )


class CofinsAliq(BaseModel):
    """COFINS taxed by rate."""

    model_config = _CONFIG

    cst: Literal["01", "02"] = Field(
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    v_bc: str = Field(
        validation_alias=AliasChoices("v_bc", "vBC"),
        serialization_alias="vBC",
    )
    p_cofins: str = Field(
        validation_alias=AliasChoices("p_cofins", "pCOFINS"),
        serialization_alias="pCOFINS",
    )
    v_cofins: str = Field(
        validation_alias=AliasChoices("v_cofins", "vCOFINS"),
        serialization_alias="vCOFINS",
    )


class CofinsQtde(BaseModel):
    """COFINS taxed by quantity."""

    model_config = _CONFIG

    cst: Literal["03"] = Field(
        default="03",
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    q_bc_prod: str = Field(
        validation_alias=AliasChoices("q_bc_prod", "qBCProd"),
        serialization_alias="qBCProd",
    )
    v_aliq_prod: str = Field(
        validation_alias=AliasChoices("v_aliq_prod", "vAliqProd"),
        serialization_alias="vAliqProd",
    )
    v_cofins: str = Field(
        validation_alias=AliasChoices("v_cofins", "vCOFINS"),
        serialization_alias="vCOFINS",
    )


class CofinsNt(BaseModel):
    """COFINS not taxed."""

    model_config = _CONFIG

    cst: Literal["04", "05", "06", "07", "08", "09"] = Field(
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )


class CofinsOutr(BaseModel):
    """COFINS taxed some other way."""

    model_config = _CONFIG

    cst: _CofinsOutrCst = Field(
        validation_alias=AliasChoices("cst", "CST"),
        serialization_alias="CST",
    )
    v_bc: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc", "vBC"),
        serialization_alias="vBC",
    )
    p_cofins: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_cofins", "pCOFINS"),
        serialization_alias="pCOFINS",
    )
    q_bc_prod: str | None = Field(
        default=None,
        validation_alias=AliasChoices("q_bc_prod", "qBCProd"),
        serialization_alias="qBCProd",
    )
    v_aliq_prod: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_aliq_prod", "vAliqProd"),
        serialization_alias="vAliqProd",
    )
    v_cofins: str = Field(
        validation_alias=AliasChoices("v_cofins", "vCOFINS"),
        serialization_alias="vCOFINS",
    )


class IcmsUfDest(BaseModel):
    """Interstate ICMS share owed to the destination state."""

    model_config = _CONFIG

    v_bc_uf_dest: str = Field(
        validation_alias=AliasChoices("v_bc_uf_dest", "vBCUFDest"),
        serialization_alias="vBCUFDest",
    )
    v_bc_fcp_uf_dest: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc_fcp_uf_dest", "vBCFCPUFDest"),
        serialization_alias="vBCFCPUFDest",
    )
    p_fcp_uf_dest: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_fcp_uf_dest", "pFCPUFDest"),
        serialization_alias="pFCPUFDest",
    )
    p_icms_uf_dest: str = Field(
        validation_alias=AliasChoices("p_icms_uf_dest", "pICMSUFDest"),
        serialization_alias="pICMSUFDest",
    )
    p_icms_inter: str = Field(
        validation_alias=AliasChoices("p_icms_inter", "pICMSInter"),
        serialization_alias="pICMSInter",
    )
    p_icms_inter_part: str = Field(
        validation_alias=AliasChoices("p_icms_inter_part", "pICMSInterPart"),
        serialization_alias="pICMSInterPart",
    )
    v_fcp_uf_dest: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_fcp_uf_dest", "vFCPUFDest"),
        serialization_alias="vFCPUFDest",
    )
    v_icms_uf_dest: str = Field(
        validation_alias=AliasChoices("v_icms_uf_dest", "vICMSUFDest"),
        serialization_alias="vICMSUFDest",
    )
    v_icms_uf_remet: str = Field(
        validation_alias=AliasChoices("v_icms_uf_remet", "vICMSUFRemet"),
        serialization_alias="vICMSUFRemet",
    )


class PisSt(BaseModel):
    """PIS withheld by substitution."""

    model_config = _CONFIG

    v_bc: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc", "vBC"),
        serialization_alias="vBC",
    )
    p_pis: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_pis", "pPIS"),
        serialization_alias="pPIS",
    )
    q_bc_prod: str | None = Field(
        default=None,
        validation_alias=AliasChoices("q_bc_prod", "qBCProd"),
        serialization_alias="qBCProd",
    )
    v_aliq_prod: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_aliq_prod", "vAliqProd"),
        serialization_alias="vAliqProd",
    )
    v_pis: str = Field(
        validation_alias=AliasChoices("v_pis", "vPIS"),
        serialization_alias="vPIS",
    )
    ind_soma_pis_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ind_soma_pis_st", "indSomaPISST"),
        serialization_alias="indSomaPISST",
    )


class CofinsSt(BaseModel):
    """COFINS withheld by substitution."""

    model_config = _CONFIG

    v_bc: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_bc", "vBC"),
        serialization_alias="vBC",
    )
    p_cofins: str | None = Field(
        default=None,
        validation_alias=AliasChoices("p_cofins", "pCOFINS"),
        serialization_alias="pCOFINS",
    )
    q_bc_prod: str | None = Field(
        default=None,
        validation_alias=AliasChoices("q_bc_prod", "qBCProd"),
        serialization_alias="qBCProd",
    )
    v_aliq_prod: str | None = Field(
        default=None,
        validation_alias=AliasChoices("v_aliq_prod", "vAliqProd"),
        serialization_alias="vAliqProd",
    )
    v_cofins: str = Field(
        validation_alias=AliasChoices("v_cofins", "vCOFINS"),
        serialization_alias="vCOFINS",
    )
    ind_soma_cofins_st: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ind_soma_cofins_st", "indSomaCOFINSST"),
        serialization_alias="indSomaCOFINSST",
    )


IpiVariant = IpiTrib | IpiNt | dict[str, Any]


class Ipi(BaseModel):
    """This item's IPI."""

    model_config = _CONFIG

    cnpj_prod: str | None = Field(
        default=None,
        validation_alias=AliasChoices("cnpj_prod", "CNPJProd"),
        serialization_alias="CNPJProd",
    )
    c_selo: str | None = Field(
        default=None,
        validation_alias=AliasChoices("c_selo", "cSelo"),
        serialization_alias="cSelo",
    )
    q_selo: str | None = Field(
        default=None,
        validation_alias=AliasChoices("q_selo", "qSelo"),
        serialization_alias="qSelo",
    )
    c_enq: str = Field(
        validation_alias=AliasChoices("c_enq", "cEnq"),
        serialization_alias="cEnq",
    )
    trib: IpiVariant

    def to_dict(self) -> dict:
        """Returns the IPI group as a plain dict."""
        return self.model_dump(exclude_none=True)


IcmsGroup = (
    Icms00
    | Icms02
    | Icms10
    | Icms15
    | Icms20
    | Icms30
    | Icms40
    | Icms51
    | Icms53
    | Icms60
    | Icms61
    | Icms70
    | Icms90
    | IcmsPart
    | IcmsSt
    | IcmsSn101
    | IcmsSn102
    | IcmsSn201
    | IcmsSn202
    | IcmsSn500
    | IcmsSn900
    | dict[str, Any]
)

PisGroup = PisAliq | PisQtde | PisNt | PisOutr | dict[str, Any]

CofinsGroup = CofinsAliq | CofinsQtde | CofinsNt | CofinsOutr | dict[str, Any]


class Tax(BaseModel):
    """This item's taxes, already computed by the caller."""

    model_config = _CONFIG

    v_tot_trib: str | None = None
    icms: IcmsGroup | None = None
    icms_uf_dest: IcmsUfDest | None = None
    ipi: Ipi | dict[str, Any] | None = None
    pis: PisGroup | None = None
    pis_st: PisSt | None = None
    cofins: CofinsGroup | None = None
    cofins_st: CofinsSt | None = None

    def to_dict(self) -> dict:
        """Returns the taxes as the snake_case dict the API takes."""
        return self.model_dump(exclude_none=True)
