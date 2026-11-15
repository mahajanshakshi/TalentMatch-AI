"""Document extraction module for PDF and DOCX formats."""

import io
from pathlib import Path
from typing import BinaryIO, Union
import pymupdf
import docx
import logging

from core.text_cleaner import clean_text

logger = logging.getLogger(__name__)


class DocumentParsingError(Exception):
    """Raised when parsing a resume file fails."""
    pass


def extract_text_from_pdf(file_source: Union[str, Path, bytes, BinaryIO]) -> tuple[str, int]:
    """
    Extract text and page count from a PDF document using PyMuPDF.
    
    Args:
        file_source: File path, raw bytes, or file-like object.
        
    Returns:
        tuple of (extracted_text, page_count)
    """
    doc = None
    try:
        if isinstance(file_source, (str, Path)):
            path_obj = Path(file_source)
            if not path_obj.exists():
                raise DocumentParsingError(f"File not found: {file_source}")
            doc = pymupdf.open(str(path_obj))
        elif isinstance(file_source, bytes):
            doc = pymupdf.open(stream=file_source, filetype="pdf")
        elif hasattr(file_source, "read"):
            data = file_source.read()
            if hasattr(file_source, "seek"):
                file_source.seek(0)
            doc = pymupdf.open(stream=data, filetype="pdf")
        else:
            raise DocumentParsingError("Unsupported file source type for PDF extraction.")

        if doc.is_encrypted:
            raise DocumentParsingError("The PDF document is encrypted or password-protected.")

        page_texts = []
        page_count = len(doc)
        for page_idx in range(page_count):
            page = doc[page_idx]
            page_text = page.get_text("text")
            if page_text:
                page_texts.append(page_text)

        full_text = "\n\n".join(page_texts)
        if not full_text.strip():
            logger.warning("PDF yielded no extractable text. It may contain scanned images.")

        return full_text, page_count

    except Exception as e:
        if isinstance(e, DocumentParsingError):
            raise
        logger.error("Failed to extract text from PDF: %s", str(e), exc_info=True)
        raise DocumentParsingError(f"Failed to parse PDF document: {str(e)}") from e
    finally:
        if doc is not None:
            doc.close()


def extract_text_from_docx(file_source: Union[str, Path, bytes, BinaryIO]) -> tuple[str, int]:
    """
    Extract text from a DOCX document using python-docx.
    Includes both body paragraphs and table cell contents.
    
    Args:
        file_source: File path, raw bytes, or file-like object.
        
    Returns:
        tuple of (extracted_text, estimated_paragraphs_count)
    """
    try:
        doc = None
        if isinstance(file_source, (str, Path)):
            path_obj = Path(file_source)
            if not path_obj.exists():
                raise DocumentParsingError(f"File not found: {file_source}")
            doc = docx.Document(str(path_obj))
        elif isinstance(file_source, bytes):
            stream = io.BytesIO(file_source)
            doc = docx.Document(stream)
        elif hasattr(file_source, "read"):
            data = file_source.read()
            if hasattr(file_source, "seek"):
                file_source.seek(0)
            stream = io.BytesIO(data)
            doc = docx.Document(stream)
        else:
            raise DocumentParsingError("Unsupported file source type for DOCX extraction.")

        content_parts = []

        # Extract text from standard paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                content_parts.append(text)

        # Extract text from tables (often used in resumes for layout/skills)
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                # Deduplicate identical adjacent cells (from merged cells)
                deduped_cells = []
                for cell_text in row_cells:
                    if not deduped_cells or deduped_cells[-1] != cell_text:
                        deduped_cells.append(cell_text)
                if deduped_cells:
                    content_parts.append(" | ".join(deduped_cells))

        full_text = "\n\n".join(content_parts)
        return full_text, len(content_parts)

    except Exception as e:
        if isinstance(e, DocumentParsingError):
            raise
        logger.error("Failed to extract text from DOCX: %s", str(e), exc_info=True)
        raise DocumentParsingError(f"Failed to parse DOCX document: {str(e)}") from e


def extract_resume_text(
    file_source: Union[str, Path, bytes, BinaryIO],
    file_name: str,
    clean: bool = True,
) -> dict:
    """
    Automatically detect file type and extract clean text from PDF or DOCX resumes.
    
    Args:
        file_source: File path, bytes, or buffer.
        file_name: Name of the file including extension.
        clean: Whether to apply text normalization.
        
    Returns:
        dict containing 'raw_text', 'cleaned_text', 'file_name', 'file_type', 'unit_count'
    """
    suffix = Path(file_name).suffix.lower()

    if suffix == ".pdf":
        raw_text, units = extract_text_from_pdf(file_source)
        file_type = "PDF"
    elif suffix in (".docx", ".doc"):
        if suffix == ".doc":
            raise DocumentParsingError(
                "Legacy .doc format is not directly supported. Please save the file as modern .docx or .pdf."
            )
        raw_text, units = extract_text_from_docx(file_source)
        file_type = "DOCX"
    else:
        raise DocumentParsingError(
            f"Unsupported file format '{suffix}'. Please upload a .pdf or .docx resume."
        )

    processed_text = clean_text(raw_text) if clean else raw_text

    if not processed_text.strip():
        raise DocumentParsingError(
            f"No readable text could be extracted from '{file_name}'. "
            "Please ensure the file is not scanned as an image or empty."
        )

    return {
        "file_name": file_name,
        "file_type": file_type,
        "raw_text": raw_text,
        "cleaned_text": processed_text,
        "unit_count": units,
        "char_count": len(processed_text),
    }

