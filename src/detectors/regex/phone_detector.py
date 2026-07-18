"""Detects phone numbers using a regular expression plus a digit-count filter.

Phone numbers are formatted too inconsistently (spaces, hyphens, optional
country code, optional area code) to match with a single tight pattern
without also missing valid numbers. Instead, a permissive pattern finds
digit-and-separator "candidates", and `_is_plausible_phone_number` rejects
any candidate whose total digit count doesn't fall in the range a real
phone number (with or without a country code) would have.

Known limitation: this can still match other 10-13 digit numeric codes
(e.g. some reference or account numbers) that happen to use phone-like
separators. See the README for the documented precision trade-off.
"""

import re

from models.entity import Entity
from utils.regex_helpers import entities_from_pattern

ENTITY_TYPE = "PHONE_NUMBER"
DETECTOR_SOURCE = "regex.phone"
CONFIDENCE_SCORE = 0.85

_MIN_PHONE_DIGITS = 10
_MAX_PHONE_DIGITS = 13

_PHONE_CANDIDATE_PATTERN = re.compile(
    r"(?<!\d)(?:\+\d{1,3}[\s-]?)?(?:\(?\d{2,5}\)?[\s-]?){1,4}\d{2,5}(?!\d)"
)


def _is_plausible_phone_number(match: re.Match[str]) -> bool:
    digit_count = len(re.sub(r"\D", "", match.group()))
    return _MIN_PHONE_DIGITS <= digit_count <= _MAX_PHONE_DIGITS


def detect_phone(text: str) -> list[Entity]:
    """Detect every phone number in `text`."""
    return entities_from_pattern(
        text,
        _PHONE_CANDIDATE_PATTERN,
        ENTITY_TYPE,
        DETECTOR_SOURCE,
        CONFIDENCE_SCORE,
        match_filter=_is_plausible_phone_number,
    )
