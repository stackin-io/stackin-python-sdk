"""Types module."""

from __future__ import annotations

from enum import Enum


class DocumentType(str, Enum):
    """Fiscal document type to issue/consult/cancel. Doubles as the
    jurisdiction selector today — both values are Brazilian (SEFAZ/UF,
    national ADN). A new country adds a member here plus a matching
    `invoice.<country>` package (see `invoice.br`) and
    `invoice-api/app/providers/<country>/`."""

    NFE = "nfe"
    NFSE = "nfse"
