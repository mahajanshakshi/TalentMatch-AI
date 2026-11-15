"""Unit tests for document parsing (PDF and DOCX)."""

import io
import pytest
import pymupdf
import docx

from core.document_parser import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_resume_text,
    DocumentParsingError,
)


@pytest.fixture
def synthetic_pdf_bytes():
    """Create an in-memory PDF document."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Jane Smith\nSenior AI Scientist\nExpert in PyTorch and LLMs.")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def synthetic_docx_bytes():
    """Create an in-memory DOCX document."""
    doc = docx.Document()
    doc.add_heading("Robert Frost", level=1)
    doc.add_paragraph("Full Stack Python Architect with 8 years of experience.")
    
    # Add a table to test table cell extraction
    table = doc.add_table(rows=1, cols=2)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Skill"
    hdr_cells[1].text = "Proficiency"
    row_cells = table.add_row().cells
    row_cells[0].text = "FastAPI"
    row_cells[1].text = "Advanced"

    stream = io.BytesIO()
    doc.save(stream)
    return stream.getvalue()


def test_extract_pdf_success(synthetic_pdf_bytes):
    text, page_count = extract_text_from_pdf(synthetic_pdf_bytes)
    assert page_count == 1
    assert "Jane Smith" in text
    assert "Senior AI Scientist" in text


def test_extract_docx_success(synthetic_docx_bytes):
    text, unit_count = extract_text_from_docx(synthetic_docx_bytes)
    assert unit_count > 0
    assert "Robert Frost" in text
    assert "Full Stack Python Architect" in text
    assert "FastAPI" in text


def test_extract_resume_text_dispatcher(synthetic_pdf_bytes, synthetic_docx_bytes):
    pdf_result = extract_resume_text(synthetic_pdf_bytes, "jane_resume.pdf")
    assert pdf_result["file_type"] == "PDF"
    assert "Jane Smith" in pdf_result["cleaned_text"]

    docx_result = extract_resume_text(synthetic_docx_bytes, "robert_resume.docx")
    assert docx_result["file_type"] == "DOCX"
    assert "Robert Frost" in docx_result["cleaned_text"]


def test_unsupported_file_extension():
    with pytest.raises(DocumentParsingError, match="Unsupported file format"):
        extract_resume_text(b"some bytes", "resume.txt")


def test_empty_document():
    doc = pymupdf.open()
    doc.new_page()  # blank page
    empty_pdf = doc.tobytes()
    doc.close()

    with pytest.raises(DocumentParsingError, match="No readable text"):
        extract_resume_text(empty_pdf, "empty.pdf")

