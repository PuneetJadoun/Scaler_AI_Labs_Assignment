"""Orchestrates replacement of detected entities in a Document.

This module is the ONLY public interface of the Replacement Module. It
knows how to locate each entity's text (paragraph or table cell), how to
keep repeated occurrences of the same original value consistent, and how
to rebuild the Document with those replacements applied. It contains no
fake-value generation logic itself — every replacer under
`replacement.replacers` owns exactly one entity type, and `faker_provider`
owns the Faker dependency.

The Document, Paragraph, Table, Row, and Cell models are all immutable
(frozen dataclasses), so "updating" them means building new instances,
not mutating the ones passed in. The original Document (and the original
.docx file) are never touched; only a new, in-memory Document is
returned. Writing that back out to a .docx file is the Writer Module's
job, not this one's.
"""

import dataclasses
import logging
from collections.abc import Callable

from document.models.cell import Cell, Row
from document.models.document import Document
from document.models.paragraph import Paragraph
from document.models.table import Table
from models.entity import PARAGRAPH_LOCATION, TABLE_CELL_LOCATION, Entity
from replacement.replacers.address_replacer import replace_address
from replacement.replacers.company_replacer import replace_company
from replacement.replacers.credit_card_replacer import replace_credit_card
from replacement.replacers.dob_replacer import replace_dob
from replacement.replacers.email_replacer import replace_email
from replacement.replacers.ip_replacer import replace_ip
from replacement.replacers.person_replacer import replace_person
from replacement.replacers.phone_replacer import replace_phone
from replacement.replacers.ssn_replacer import replace_ssn

logger = logging.getLogger(__name__)

Replacer = Callable[[Entity], str]

_REPLACERS: dict[str, Replacer] = {
    "PERSON": replace_person,
    "EMAIL": replace_email,
    "PHONE_NUMBER": replace_phone,
    "ORGANIZATION": replace_company,
    "LOCATION": replace_address,
    "SSN": replace_ssn,
    "CREDIT_CARD": replace_credit_card,
    "DATE_OF_BIRTH": replace_dob,
    "IP_ADDRESS": replace_ip,
}

# Consistency cache: the same (entity_type, detected_text) must always map
# to the same fake value within one call to replace_entities.
_ReplacementCache = dict[tuple[str, str], str]


def replace_entities(document: Document, entities: list[Entity]) -> Document:
    """Replace every detected entity's text in `document`.

    Args:
        document: The structured Document produced by document.reader.
        entities: Entities produced by detectors.detector_manager.analyze_document.

    Returns:
        A new Document with every supported entity's text replaced by a
        realistic fake value. Occurrences of the same original value (for
        the same entity type) always receive the same fake value. If
        `entities` is empty, the original `document` is returned as-is.
    """
    if not entities:
        return document

    cache: _ReplacementCache = {}
    paragraph_entities, cell_entities = _group_by_location(entities)

    paragraphs = [
        _update_paragraph(paragraph, paragraph_entities.get(paragraph.id), cache)
        for paragraph in document.paragraphs
    ]
    tables = [_update_table(table, cell_entities, cache) for table in document.tables]

    return dataclasses.replace(document, paragraphs=paragraphs, tables=tables)


def _group_by_location(
    entities: list[Entity],
) -> tuple[dict[int, list[Entity]], dict[tuple[int, int, int], list[Entity]]]:
    """Split entities into paragraph-indexed and cell-indexed groups."""
    paragraph_entities: dict[int, list[Entity]] = {}
    cell_entities: dict[tuple[int, int, int], list[Entity]] = {}

    for entity in entities:
        if entity.location_type == PARAGRAPH_LOCATION:
            paragraph_entities.setdefault(entity.paragraph_index, []).append(entity)
        elif entity.location_type == TABLE_CELL_LOCATION:
            key = (entity.table_index, entity.row_index, entity.cell_index)
            cell_entities.setdefault(key, []).append(entity)
        else:
            logger.warning("Entity has no location; skipping: %r", entity)

    return paragraph_entities, cell_entities


def _update_paragraph(
    paragraph: Paragraph, entities: list[Entity] | None, cache: _ReplacementCache
) -> Paragraph:
    if not entities:
        return paragraph
    new_text = _apply_replacements(paragraph.text, entities, cache)
    return dataclasses.replace(paragraph, text=new_text)


def _update_table(
    table: Table,
    cell_entities: dict[tuple[int, int, int], list[Entity]],
    cache: _ReplacementCache,
) -> Table:
    rows = [_update_row(table.id, row, cell_entities, cache) for row in table.rows]
    return dataclasses.replace(table, rows=rows)


def _update_row(
    table_id: int,
    row: Row,
    cell_entities: dict[tuple[int, int, int], list[Entity]],
    cache: _ReplacementCache,
) -> Row:
    cells = [
        _update_cell(table_id, row.id, cell, cell_entities, cache) for cell in row.cells
    ]
    return dataclasses.replace(row, cells=cells)


def _update_cell(
    table_id: int,
    row_id: int,
    cell: Cell,
    cell_entities: dict[tuple[int, int, int], list[Entity]],
    cache: _ReplacementCache,
) -> Cell:
    entities = cell_entities.get((table_id, row_id, cell.id))
    if not entities:
        return cell
    new_text = _apply_replacements(cell.text, entities, cache)
    return dataclasses.replace(cell, text=new_text)


def _apply_replacements(text: str, entities: list[Entity], cache: _ReplacementCache) -> str:
    """Replace every entity's span in `text`, right-to-left so earlier offsets stay valid."""
    result = text
    consumed_start: int | None = None

    for entity in sorted(entities, key=lambda e: e.start_offset, reverse=True):
        if consumed_start is not None and entity.end_offset > consumed_start:
            logger.warning(
                "Entity %r overlaps an already-replaced span; skipping.", entity
            )
            continue

        replacement = _get_replacement(entity, cache)
        result = result[: entity.start_offset] + replacement + result[entity.end_offset :]
        consumed_start = entity.start_offset

    return result


def _get_replacement(entity: Entity, cache: _ReplacementCache) -> str:
    """Return a consistent fake value for `entity`, generating and caching it if new."""
    key = (entity.entity_type, entity.detected_text)
    if key in cache:
        return cache[key]

    replacer = _REPLACERS.get(entity.entity_type)
    if replacer is None:
        logger.warning("No replacer for entity type '%s'; leaving text unchanged.", entity.entity_type)
        return entity.detected_text

    try:
        replacement = replacer(entity)
    except Exception:
        logger.warning(
            "Replacer for entity type '%s' failed; leaving text unchanged.",
            entity.entity_type,
            exc_info=True,
        )
        return entity.detected_text

    cache[key] = replacement
    return replacement
