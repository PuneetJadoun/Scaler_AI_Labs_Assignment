"""Detects US Social Security Numbers using a regular expression.

Format: AAA-GG-SSSS (area-group-serial), e.g. 123-45-6789. Only the
hyphenated form is matched; excludes area 000/666/900-999, group 00, and
serial 0000, which are never issued.
"""

import re

from models.entity import Entity
from utils.regex_helpers import entities_from_pattern

ENTITY_TYPE = "SSN"
DETECTOR_SOURCE = "regex.ssn"
CONFIDENCE_SCORE = 0.9

_SSN_PATTERN = re.compile(r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b")


def detect_ssn(text: str) -> list[Entity]:
    """Detect every SSN in `text`."""
    return entities_from_pattern(text, _SSN_PATTERN, ENTITY_TYPE, DETECTOR_SOURCE, CONFIDENCE_SCORE)
