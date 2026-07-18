"""Detects email addresses using a regular expression."""

import re

from models.entity import Entity
from utils.regex_helpers import entities_from_pattern

ENTITY_TYPE = "EMAIL"
DETECTOR_SOURCE = "regex.email"
CONFIDENCE_SCORE = 0.95

_EMAIL_PATTERN = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)


def detect_email(text: str) -> list[Entity]:
    """Detect every email address in `text`."""
    return entities_from_pattern(text, _EMAIL_PATTERN, ENTITY_TYPE, DETECTOR_SOURCE, CONFIDENCE_SCORE)
