"""Token counting and context budgeting utilities."""

import logging

logger = logging.getLogger(__name__)

_ENCODER = None


def get_encoder():
    """Lazily load tiktoken encoder with fallback."""
    global _ENCODER
    if _ENCODER is None:
        try:
            import tiktoken
            _ENCODER = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.debug("tiktoken encoder could not be loaded: %s", e)
            _ENCODER = False
    return _ENCODER


def count_tokens(text: str) -> int:
    """
    Count or estimate the number of tokens in a text string.
    
    Args:
        text: Input string.
        
    Returns:
        Token count (exact via tiktoken or estimated via words heuristic).
    """
    if not text:
        return 0

    encoder = get_encoder()
    if encoder:
        try:
            return len(encoder.encode(text, disallowed_special=()))
        except Exception:
            pass

    # Fallback heuristic: 1 token ~= 4 characters or ~0.75 words
    words = len(text.split())
    chars = len(text)
    return max(int(words * 1.3), int(chars / 4))

