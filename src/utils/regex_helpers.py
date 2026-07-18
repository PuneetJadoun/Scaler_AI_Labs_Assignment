"""Shared helpers for building Entity results from regex matches.

Used by every detector in `detectors.regex` so each one only has to define
its pattern (and, where needed, a validation filter) instead of repeating
the match-to-Entity conversion.
"""

import re
from collections.abc import Callable, Iterable

from models.entity import Entity

MatchFilter = Callable[[re.Match[str]], bool]


def entity_from_match(
    match: re.Match[str],
    entity_type: str,
    detector_source: str,
    confidence_score: float,
) -> Entity:
    """Wrap a single regex match in an Entity (location fields left unset)."""
    return Entity(
        detected_text=match.group(),
        entity_type=entity_type,
        confidence_score=confidence_score,
        detector_source=detector_source,
        start_offset=match.start(),
        end_offset=match.end(),
    )


def entities_from_pattern(
    text: str,
    pattern: re.Pattern[str],
    entity_type: str,
    detector_source: str,
    confidence_score: float,
    match_filter: MatchFilter | None = None,
) -> list[Entity]:
    """Find every match of `pattern` in `text` and convert it to an Entity.

    Args:
        text: Plain text to search.
        pattern: Compiled regex identifying candidate matches.
        entity_type: PII category to assign to every resulting Entity.
        detector_source: Identifier of the calling detector.
        confidence_score: Confidence to assign to every resulting Entity.
        match_filter: Optional predicate to reject candidate matches that
            the pattern alone cannot rule out (e.g. a checksum check).

    Returns:
        One Entity per accepted match, in the order they appear in text.
    """
    matches: Iterable[re.Match[str]] = pattern.finditer(text)
    if match_filter is not None:
        matches = (match for match in matches if match_filter(match))

    return [
        entity_from_match(match, entity_type, detector_source, confidence_score)
        for match in matches
    ]
