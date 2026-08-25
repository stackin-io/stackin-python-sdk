"""Invoice document module — Argentina-specific, see `invoice.core.ar`."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class InvoiceClass(str, Enum):
    """
    Comprobante class — not confirmed against an official ARCA table,
    see `invoice-api/plan/ARGENTINA.md`.

    A: Responsable Inscripto -> another Responsable Inscripto.
    B: Responsable Inscripto -> final consumer/exempt.
    C: Monotributista/exempt -> any customer.
    E: Export.
    """

    A = "A"
    B = "B"
    C = "C"
    E = "E"


class InvoiceDocument(BaseModel):
    """
    Details for an Argentine comprobante ("factura") — **not** a generic
    concept, `invoice_class`/`point_of_sale` have no meaning outside
    Argentina's WSFEv1. Mirrors `invoice.br.Product`'s role for NFE.

    **Not usable yet** — `invoice-api` has no `DocumentType` for
    Argentina (`app/providers/ar/wsfe/` is a scaffold that refuses to
    authorize anything, see `invoice-api/plan/ARGENTINA.md`). This
    class exists so the shape is ready once that's implemented.

    Args:
        invoice_class (InvoiceClass | None): A/B/C/E.
        point_of_sale (int | None): Punto de venta.
        customer_document (str | None): Customer's document number.
        document_type (str | None): Customer document type — "DNI",
            "CUIT", etc. (real WSFEv1 codes not confirmed).
    """

    invoice_class: InvoiceClass | None = Field(default=None)
    point_of_sale: int | None = Field(default=None)
    customer_document: str | None = Field(default=None)
    document_type: str | None = Field(default=None)

    def to_dict(self) -> dict:
        """Return the invoice document's details as a plain dict —
        fields left unset are omitted, not sent as null."""
        return self.model_dump(exclude_none=True)
