"""Detects credit card numbers using a regular expression plus a Luhn check.

A permissive pattern finds digit-and-separator candidates of plausible
length (13-19 digits, optionally grouped e.g. 4111 1111 1111 1111); the
Luhn checksum then rejects any candidate that isn't a structurally valid
card number, which meaningfully reduces false positives compared to a
pattern alone.
"""

import re

from models.entity import Entity
from utils.regex_helpers import entities_from_pattern

ENTITY_TYPE = "CREDIT_CARD"
DETECTOR_SOURCE = "regex.credit_card"
CONFIDENCE_SCORE = 0.9

_MIN_CARD_DIGITS = 13
_MAX_CARD_DIGITS = 19

_CREDIT_CARD_CANDIDATE_PATTERN = re.compile(
    r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{1,7}(?!\d)"
)


def _passes_luhn_check(match: re.Match[str]) -> bool:
    digits = re.sub(r"\D", "", match.group())
    if not (_MIN_CARD_DIGITS <= len(digits) <= _MAX_CARD_DIGITS):
        return False

    total = 0
    for index, char in enumerate(reversed(digits)):
        digit = int(char)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def detect_credit_card(text: str) -> list[Entity]:
    """Detect every credit card number in `text`."""
    return entities_from_pattern(
        text,
        _CREDIT_CARD_CANDIDATE_PATTERN,
        ENTITY_TYPE,
        DETECTOR_SOURCE,
        CONFIDENCE_SCORE,
        match_filter=_passes_luhn_check,
    )
