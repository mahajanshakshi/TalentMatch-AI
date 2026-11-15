"""Text cleaning, sanitization, and normalization utilities."""

import re
import unicodedata
import logging

logger = logging.getLogger(__name__)

# Common bullet points in resumes
BULLET_PATTERN = re.compile(r"[\u2022\u2023\u25aa\u25ab\u25cf\u25cb\u25e6\u2219\u00b7\uf0b7\uf0a7\u25fe\u25fd]+")
MULTI_SPACE_PATTERN = re.compile(r"[ \t]+")
MULTI_NEWLINE_PATTERN = re.compile(r"\n\s*\n\s*\n+")
NON_PRINTABLE_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


def clean_text(raw_text: str, max_chars: int = 50000) -> str:
    """
    Clean, normalize, and sanitize raw extracted resume or JD text.
    
    Args:
        raw_text: The raw string extracted from document or user input.
        max_chars: Safety cap on text length to prevent context explosion.
        
    Returns:
        Cleaned, readable string preserving section structure.
    """
    if not raw_text or not isinstance(raw_text, str):
        return ""

    # Normalize unicode (NFKC turns special unicode ligatures like 'fi' into standard chars)
    text = unicodedata.normalize("NFKC", raw_text)

    # Strip control/non-printable characters
    text = NON_PRINTABLE_PATTERN.sub("", text)

    # Replace carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Normalize weird bullet characters to standard markdown dash
    text = BULLET_PATTERN.sub("\n- ", text)

    # Standardize multiple inline spaces & tabs to a single space
    lines = []
    for line in text.split("\n"):
        cleaned_line = MULTI_SPACE_PATTERN.sub(" ", line).strip()
        lines.append(cleaned_line)

    text = "\n".join(lines)

    # Collapse excessive consecutive empty lines (max 2)
    text = MULTI_NEWLINE_PATTERN.sub("\n\n", text)

    # Strip leading/trailing whitespaces
    text = text.strip()

    # Safety truncate if text exceeds maximum character budget
    if len(text) > max_chars:
        logger.warning(
            "Text length (%d chars) exceeded maximum limit (%d). Truncating.",
            len(text),
            max_chars,
        )
        text = text[:max_chars] + "\n\n[... Truncated for token limit ...]"

    return text

