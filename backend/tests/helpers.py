"""Shared test helpers — importable from any test module.

conftest.py is auto-loaded by pytest but is NOT importable as a regular module.
Utility functions that are needed both in conftest.py and in test files go here.
"""

from __future__ import annotations

import io


def make_blank_pdf(num_pages: int = 1) -> bytes:
    """Create a valid but blank (no text) PDF using pypdf PdfWriter.

    pypdf is a production dependency, so using it here avoids adding a
    test-only PDF generation library. Blank pages are sufficient for:
        - Testing PDF header validation (valid %PDF- magic bytes)
        - Testing page count extraction
        - Testing ExtractedPage.is_empty behaviour (all pages will be empty)

    For tests that need PDFs with extractable text, mock PDFService instead
    and return a pre-built ExtractedDocument with the desired text.
    """
    from pypdf import PdfWriter

    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()
