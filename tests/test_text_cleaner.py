"""Unit tests for text cleaning and sanitization."""

import pytest
from core.text_cleaner import clean_text


def test_clean_text_basic():
    raw = "John   Doe  \t\t\nSoftware   Engineer"
    cleaned = clean_text(raw)
    assert "John Doe" in cleaned
    assert "Software Engineer" in cleaned


def test_clean_text_bullet_normalization():
    raw = "Skills:\n• Python\n▪ PyTorch\n* Docker\n⁃ Kubernetes"
    cleaned = clean_text(raw)
    assert "- Python" in cleaned
    assert "- PyTorch" in cleaned


def test_clean_text_control_characters():
    raw = "Hello\x00\x07World\nTest\x0bString"
    cleaned = clean_text(raw)
    assert "\x00" not in cleaned
    assert "\x07" not in cleaned
    assert "HelloWorld" in cleaned or "Hello" in cleaned


def test_clean_text_empty_and_none():
    assert clean_text("") == ""
    assert clean_text(None) == ""


def test_clean_text_truncation():
    long_text = "A" * 1000
    cleaned = clean_text(long_text, max_chars=100)
    assert len(cleaned) < 200
    assert "[... Truncated" in cleaned

