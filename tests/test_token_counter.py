"""Unit tests for token counter utility."""

from core.token_counter import count_tokens


def test_token_counter_empty():
    assert count_tokens("") == 0
    assert count_tokens(None) == 0


def test_token_counter_text():
    sample_text = "This is a sample sentence designed to test token counting in TalentMatch AI."
    tokens = count_tokens(sample_text)
    assert tokens > 5
    assert tokens < 50

