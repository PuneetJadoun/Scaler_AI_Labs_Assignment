"""Orchestrates every detector over a Document and returns detected entities.

This module is the ONLY public interface of the Detector Module. It knows
how to traverse a Document's paragraphs and tables and how to attach
location metadata to whatever a detector finds, but it contains no PII
matching logic of its own — every pattern and every NLP call lives in the
individual detector modules under `detectors.regex` and `detectors.ner`.
"""

import dataclasses
import logging
from collections.abc import Callable

from detectors.ner.presidio_detector import detect_entities as detect_presidio_entities
from detectors.regex.credit_card_detector import detect_credit_card
from detectors.regex.dob_detector import detect_dob
from detectors.regex.email_detector import detect_email
from detectors.regex.ip_detector import detect_ip
from detectors.regex.phone_detector import detect_phone
from detectors.regex.ssn_detector import detect_ssn
from document.models.document import Document
from models.entity import PARAGRAPH_LOCATION, TABLE_CELL_LOCATION, Entity

logger = logging.getLogger(__name__)

Detector = Callable[[str], list[Entity]]

_REGEX_DETECTORS: list[Detector] = [
    detect_email,
    detect_phone,
    detect_ssn,
    detect_credit_card,
    detect_dob,
    detect_ip,
]

_ALL_DETECTORS: list[Detector] = [*_REGEX_DETECTORS, detect_presidio_entities]


def analyze_document(document: Document) -> list[Entity]:
    """Run every detector over `document` and return all detected entities.

    Traverses every paragraph and every table cell, passes each piece of
    text to every detector, stamps the resulting entities with where in
    the document they came from, and removes exact duplicate detections.

    Args:
        document: The structured Document produced by document.reader.

    Returns:
        A flat, de-duplicated list of located Entity objects. Empty if the
        document has no paragraphs or tables, or if nothing was detected.
    """
    entities: list[Entity] = []

    for paragraph in document.paragraphs:
        entities.extend(
            _detect_in_text(
                paragraph.text,
                location_type=PARAGRAPH_LOCATION,
                paragraph_index=paragraph.id,
            )
        )

    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                entities.extend(
                    _detect_in_text(
                        cell.text,
                        location_type=TABLE_CELL_LOCATION,
                        table_index=table.id,
                        row_index=row.id,
                        cell_index=cell.id,
                    )
                )

    return _deduplicate(entities)


def _detect_in_text(text: str, **location: int | str | None) -> list[Entity]:
    """Run every detector over one piece of text and stamp the results with `location`."""
    if not text or not text.strip():
        return []

    raw_entities: list[Entity] = []
    for detector in _ALL_DETECTORS:
        raw_entities.extend(_run_detector(detector, text))

    return [dataclasses.replace(entity, **location) for entity in raw_entities]


def _run_detector(detector: Detector, text: str) -> list[Entity]:
    """Call `detector` defensively so one bad detector can't break the whole run."""
    try:
        results = detector(text)
    except Exception:
        logger.warning(
            "Detector '%s' raised an exception; skipping its results.",
            getattr(detector, "__name__", detector),
            exc_info=True,
        )
        return []

    if not isinstance(results, list) or not all(isinstance(item, Entity) for item in results):
        logger.warning(
            "Detector '%s' returned an invalid result; skipping its results.",
            getattr(detector, "__name__", detector),
        )
        return []

    return results


def _deduplicate(entities: list[Entity]) -> list[Entity]:
    """Collapse entities that agree on type, span, and location to a single one.

    Different detectors can legitimately flag the same exact span with the
    same entity type (e.g. two regex detectors matching an overlapping
    pattern). When that happens, keep only the highest-confidence result.
    Entities that merely overlap but disagree on type are left as-is: that
    ambiguity is meaningful information, not noise to discard here.
    """
    best_by_key: dict[tuple, Entity] = {}
    for entity in entities:
        key = (
            entity.location_type,
            entity.paragraph_index,
            entity.table_index,
            entity.row_index,
            entity.cell_index,
            entity.start_offset,
            entity.end_offset,
            entity.entity_type,
        )
        existing = best_by_key.get(key)
        if existing is None or entity.confidence_score > existing.confidence_score:
            best_by_key[key] = entity

    return list(best_by_key.values())
