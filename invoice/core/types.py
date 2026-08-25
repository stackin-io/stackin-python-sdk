"""Types module."""

from __future__ import annotations

from enum import Enum


class DocumentType(str, Enum):
    """Fiscal document type to issue/consult/cancel — both Brazilian
    (NFE via SEFAZ/UF, NFSE via the national ADN). Doubles as the
    jurisdiction selector today since only Brazil is implemented on
    the API side (`app/providers/br/`)."""

    NFE = "nfe"
    NFSE = "nfse"
