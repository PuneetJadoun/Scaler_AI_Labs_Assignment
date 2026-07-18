"""Reusable model representing one detected piece of PII."""

from dataclasses import dataclass

PARAGRAPH_LOCATION = "paragraph"
TABLE_CELL_LOCATION = "table_cell"


@dataclass(frozen=True)
class Entity:
    """One PII entity detected somewhere in a document.

    An Entity captures two things: what was found (the text, its type,
    how confident the detector is, and which detector found it) and where
    it was found (which paragraph or table/row/cell, plus the character
    offsets within that piece of text). The Replacement Module will use
    the "what" to pick a consistent fake value and the "where" to write
    that value back into the correct location.

    Detectors themselves only know about a single string of text, so they
    construct an Entity with the location fields left at their defaults;
    the Detector Manager fills those in as it traverses the Document.

    Attributes:
        detected_text: The exact substring flagged as PII.
        entity_type: Category of PII, e.g. "EMAIL", "PERSON", "PAN". A
            plain string rather than an Enum so a new detector can
            introduce a new type without modifying this shared model.
        confidence_score: Detector's confidence, in the range [0.0, 1.0].
        detector_source: Identifies which detector produced this entity,
            e.g. "regex.email" or "presidio".
        start_offset: Start character offset of detected_text within the
            source paragraph/cell text.
        end_offset: End character offset (exclusive) of detected_text
            within the source paragraph/cell text.
        location_type: Either PARAGRAPH_LOCATION or TABLE_CELL_LOCATION,
            filled in by the Detector Manager. None until then.
        paragraph_index: Index of the source paragraph, when
            location_type is PARAGRAPH_LOCATION; otherwise None.
        table_index: Index of the source table, when location_type is
            TABLE_CELL_LOCATION; otherwise None.
        row_index: Index of the source row, when location_type is
            TABLE_CELL_LOCATION; otherwise None.
        cell_index: Index of the source cell, when location_type is
            TABLE_CELL_LOCATION; otherwise None.
    """

    detected_text: str
    entity_type: str
    confidence_score: float
    detector_source: str
    start_offset: int
    end_offset: int
    location_type: str | None = None
    paragraph_index: int | None = None
    table_index: int | None = None
    row_index: int | None = None
    cell_index: int | None = None
