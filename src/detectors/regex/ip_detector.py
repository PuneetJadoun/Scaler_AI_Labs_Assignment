"""Detects IPv4 addresses using a regular expression.

Each octet is bounded to 0-255, so e.g. "999.999.999.999" is correctly
rejected. IPv6 is out of scope for now (see the README's future work).
"""

import re

from models.entity import Entity
from utils.regex_helpers import entities_from_pattern

ENTITY_TYPE = "IP_ADDRESS"
DETECTOR_SOURCE = "regex.ip"
CONFIDENCE_SCORE = 0.95

_IPV4_OCTET = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
_IPV4_PATTERN = re.compile(rf"\b(?:{_IPV4_OCTET}\.){{3}}{_IPV4_OCTET}\b")


def detect_ip(text: str) -> list[Entity]:
    """Detect every IPv4 address in `text`."""
    return entities_from_pattern(text, _IPV4_PATTERN, ENTITY_TYPE, DETECTOR_SOURCE, CONFIDENCE_SCORE)
