"""Types module."""

from __future__ import annotations

from enum import Enum


class DocumentType(str, Enum):
    """The kind of fiscal document to issue, consult, or cancel."""

    NFE = "nfe"
    NFSE = "nfse"


class Environment(str, Enum):
    """Which host to talk to — pass to `Invoice(environment=...)`
    instead of a raw `base_url`. `TEST` and `PRODUCTION` resolve to the
    same host: homologation vs. production invoicing is a per-company
    setting on the platform side, not a different SDK host."""

    LOCAL = "local"
    TEST = "test"
    PRODUCTION = "production"
