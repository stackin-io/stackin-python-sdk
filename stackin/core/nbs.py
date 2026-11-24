"""The NBS suggestions of `GET /service-codes/{service_code}/nbs`.

Responses ignore the fields the API adds later, so an older SDK keeps
reading a newer API.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class NbsSuggestion(BaseModel):
    """One NFS-e Anexo VIII row for a service code's LC 116 subitem."""

    model_config = ConfigDict(extra="ignore")

    nbs: str
    description: str | None = None
    operation_indicator: str | None = None
    ibs_cbs_classification: str | None = None
    classification_name: str | None = None


class ReferenceSource(BaseModel):
    """The official file the suggestions were loaded from."""

    model_config = ConfigDict(extra="ignore")

    path: str
    date: str | None = None


class NbsSuggestions(BaseModel):
    """What Anexo VIII lists for a service code; empty when it lists none."""

    model_config = ConfigDict(extra="ignore")

    service_code: str
    suggestions: list[NbsSuggestion]
    source: ReferenceSource
