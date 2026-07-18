"""Detects date-of-birth-shaped dates using a regular expression.

Matches numeric dates (e.g. 12/04/1990, 12-04-1990), day-first month-name
dates (e.g. 12th April 1990, 12 Apr 1990), and month-first month-name
dates (e.g. April 12, 1990, May 6 2025) — the format used throughout
real-world documents such as this project's sample prospectus.

Known limitation: regex can recognize the *shape* of a date but has no way
to know whether a given date is a date of birth versus, say, a filing date
or an agreement date. Every date-shaped string in the text will be
flagged; disambiguating "is this a DOB" is left as a documented precision
trade-off (see the README).
"""

import re

from models.entity import Entity
from utils.regex_helpers import entities_from_pattern

ENTITY_TYPE = "DATE_OF_BIRTH"
DETECTOR_SOURCE = "regex.dob"
CONFIDENCE_SCORE = 0.6

_MONTH_NAMES = (
    r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
)
_NUMERIC_DATE = r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
_DAY_FIRST_DATE = rf"\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{_MONTH_NAMES})\s+\d{{4}}"
_MONTH_FIRST_DATE = rf"(?:{_MONTH_NAMES})\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}"
_DATE_PATTERN = re.compile(
    rf"\b(?:{_NUMERIC_DATE}|{_DAY_FIRST_DATE}|{_MONTH_FIRST_DATE})\b", re.IGNORECASE
)


def detect_dob(text: str) -> list[Entity]:
    """Detect every date-shaped string in `text`."""
    return entities_from_pattern(text, _DATE_PATTERN, ENTITY_TYPE, DETECTOR_SOURCE, CONFIDENCE_SCORE)
