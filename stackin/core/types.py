"""Types module."""

from __future__ import annotations

from enum import Enum


class DocumentType(str, Enum):
    """The kind of fiscal document to issue, consult, or cancel."""

    NFE = "nfe"
    NFSE = "nfse"


class Environment(str, Enum):
    """Which host to talk to, instead of a raw `base_url`."""

    LOCAL = "local"
    TEST = "test"
    PRODUCTION = "production"


class Manifestation(str, Enum):
    """The recipient's four possible answers to a received document."""

    CONFIRMACAO = "210200"
    CIENCIA = "210210"
    DESCONHECIMENTO = "210220"
    OPERACAO_NAO_REALIZADA = "210240"
