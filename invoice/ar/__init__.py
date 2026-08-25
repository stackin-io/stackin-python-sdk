"""Argentina (AR) jurisdiction — public surface, mirrors `invoice.br`.
Import from here, not from `invoice` directly:

    from invoice.ar import InvoiceDocument, InvoiceClass

**Scaffold only** — not usable with `Invoice.issue()` yet, see
`invoice.core.ar`'s docstring and `invoice-api/plan/ARGENTINA.md`.
"""

from invoice.core.ar.invoice_document import InvoiceClass, InvoiceDocument

__all__ = ["InvoiceDocument", "InvoiceClass"]
