"""Manual validation script for the Replacement Module.

This is NOT the final application and NOT a pytest/unittest suite. It is a
temporary, human-readable script that runs Reader -> Detector -> Replacement
over a real Document and reports every replacement that resulted, before
the Writer Module is built on top of it. The Writer is never invoked and no
.docx file is written; everything happens in memory.

Every replacement value is captured directly from the Replacement Module's
own replacer functions as they run (see `capture_replacements`), rather
than reverse-engineered by diffing before/after text. Diffing text this
size turns out to be unreliable: this document is boilerplate-heavy legal
text where short phrases repeat throughout a paragraph and Faker-generated
values can coincidentally collide with real words (e.g. a fake month name
matching one already in the text), which defeats both substring-anchor
search and `difflib`-style sequence alignment. Reading the value straight
from the replacer call sidesteps that problem entirely.

Usage:
    python tests/validate_replacement.py [path/to/file.docx]

If no path is given, the first .docx file found in input/ is used.
"""

from __future__ import annotations

import dataclasses
import logging
import sys
from collections import defaultdict
from pathlib import Path

# The source document can contain characters (e.g. the Rupee sign, U+20B9)
# that fall outside Windows' default console/redirect encoding (cp1252),
# which would otherwise crash mid-report with a UnicodeEncodeError.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import replacement.replacement_manager as replacement_manager  # noqa: E402
from detectors.detector_manager import analyze_document  # noqa: E402
from document.models.document import Document  # noqa: E402
from document.reader import DocumentReaderError, read_document  # noqa: E402
from models.entity import PARAGRAPH_LOCATION, TABLE_CELL_LOCATION, Entity  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

INPUT_DIR = PROJECT_ROOT / "input"
SEPARATOR = "=" * 60
DIVIDER = "-" * 40

_SUMMARY_LABELS: dict[str, str] = {
    "PERSON": "Persons Replaced",
    "EMAIL": "Emails Replaced",
    "PHONE_NUMBER": "Phone Numbers Replaced",
    "ORGANIZATION": "Companies Replaced",
    "LOCATION": "Addresses Replaced",
    "SSN": "SSNs Replaced",
    "CREDIT_CARD": "Credit Cards Replaced",
    "DATE_OF_BIRTH": "DOBs Replaced",
    "IP_ADDRESS": "IP Addresses Replaced",
}

#: (entity_type, detected_text) — the exact key replacement_manager itself
#: caches on, so grouping by it tells us which occurrences *should* end up
#: with an identical replacement.
ReplacementKey = tuple[str, str]


@dataclasses.dataclass(frozen=True)
class ReplacementRecord:
    """One unique (entity_type, detected_text) pair and the value it was replaced with."""

    entity_type: str
    original_text: str
    replacement_text: str
    detector_source: str
    occurrences: tuple[Entity, ...]


def find_input_document() -> Path:
    """Return the document to validate: a CLI arg, or the first .docx in input/."""
    if len(sys.argv) > 1:
        return Path(sys.argv[1])

    candidates = sorted(INPUT_DIR.glob("*.docx"))
    if not candidates:
        raise FileNotFoundError(
            f"No .docx file found in '{INPUT_DIR}'. "
            f"Place a document there or pass a path as an argument."
        )
    return candidates[0]


def format_source(entity: Entity) -> str:
    """Human-readable detector source, e.g. 'Regex (regex.email)' or 'Presidio'."""
    if entity.detector_source.startswith("regex."):
        return f"Regex ({entity.detector_source})"
    return "Presidio"


def location_of(entity: Entity) -> str:
    """Human-readable location string, e.g. 'Paragraph 15' or 'Table 3 Row 2 Cell 1'."""
    if entity.location_type == PARAGRAPH_LOCATION:
        return f"Paragraph {entity.paragraph_index}"
    return f"Table {entity.table_index} Row {entity.row_index} Cell {entity.cell_index}"


def group_by_paragraph(entities: list[Entity]) -> dict[int, list[Entity]]:
    """Group entities by paragraph_index, ignoring table-cell entities."""
    groups: dict[int, list[Entity]] = {}
    for entity in entities:
        if entity.location_type == PARAGRAPH_LOCATION:
            groups.setdefault(entity.paragraph_index, []).append(entity)
    return groups


def group_by_cell(entities: list[Entity]) -> dict[tuple[int, int, int], list[Entity]]:
    """Group entities by (table_index, row_index, cell_index), ignoring paragraph entities."""
    groups: dict[tuple[int, int, int], list[Entity]] = {}
    for entity in entities:
        if entity.location_type == TABLE_CELL_LOCATION:
            key = (entity.table_index, entity.row_index, entity.cell_index)
            groups.setdefault(key, []).append(entity)
    return groups


def _flatten_cells(document: Document) -> dict[tuple[int, int, int], str]:
    """Map every (table_id, row_id, cell_id) to its cell text."""
    cells: dict[tuple[int, int, int], str] = {}
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                cells[(table.id, row.id, cell.id)] = cell.text
    return cells


def _eligible_entities(entities: list[Entity]) -> tuple[list[Entity], int]:
    """Return the entities replacement_manager would actually attempt to replace.

    Mirrors the overlap handling in replacement_manager._apply_replacements
    (per paragraph/cell, sorted by start_offset, right-to-left, skipping
    spans that overlap one already kept) so "eligible" here means the same
    thing it means inside the real module. Returns the eligible entities
    plus how many were dropped as overlaps.
    """
    eligible: list[Entity] = []
    overlap_skipped = 0

    for group in [*group_by_paragraph(entities).values(), *group_by_cell(entities).values()]:
        ordered = sorted(group, key=lambda e: e.start_offset, reverse=True)
        consumed_start: int | None = None
        kept_this_group: list[Entity] = []
        for entity in ordered:
            if consumed_start is not None and entity.end_offset > consumed_start:
                overlap_skipped += 1
                continue
            kept_this_group.append(entity)
            consumed_start = entity.start_offset
        eligible.extend(kept_this_group)

    return eligible, overlap_skipped


def capture_replacements(
    document: Document, entities: list[Entity]
) -> tuple[Document, dict[ReplacementKey, str]]:
    """Run the real Replacement Module while recording each value it computes.

    Every function in replacement_manager._REPLACERS is wrapped so that,
    the moment it actually produces a fake value for some entity, that
    value is recorded under the same (entity_type, detected_text) key the
    module's own consistency cache uses. Because the cache short-circuits
    repeat keys before they ever reach the replacer, this captures exactly
    one authoritative value per key with no risk of misreading it back out
    of the rewritten document text.
    """
    captured: dict[ReplacementKey, str] = {}
    original_replacers = dict(replacement_manager._REPLACERS)

    def wrap(replacer):
        def wrapped(entity: Entity) -> str:
            result = replacer(entity)
            captured[(entity.entity_type, entity.detected_text)] = result
            return result

        return wrapped

    replacement_manager._REPLACERS = {
        entity_type: wrap(replacer) for entity_type, replacer in original_replacers.items()
    }
    try:
        replaced_document = replacement_manager.replace_entities(document, entities)
    finally:
        replacement_manager._REPLACERS = original_replacers

    return replaced_document, captured


def build_records(
    eligible_entities: list[Entity], captured: dict[ReplacementKey, str]
) -> tuple[list[ReplacementRecord], list[ReplacementKey]]:
    """Group eligible entities by replacement key and pair each with its captured value.

    Returns the records plus the list of keys that had eligible entities
    but no captured value (the replacer was missing or failed for every
    occurrence of that key).
    """
    occurrences_by_key: dict[ReplacementKey, list[Entity]] = defaultdict(list)
    for entity in eligible_entities:
        occurrences_by_key[(entity.entity_type, entity.detected_text)].append(entity)

    records: list[ReplacementRecord] = []
    missing_keys: list[ReplacementKey] = []
    for key, occurrences in occurrences_by_key.items():
        entity_type, original_text = key
        if key not in captured:
            missing_keys.append(key)
            continue
        records.append(
            ReplacementRecord(
                entity_type=entity_type,
                original_text=original_text,
                replacement_text=captured[key],
                detector_source=format_source(occurrences[0]),
                occurrences=tuple(occurrences),
            )
        )

    return records, missing_keys


def print_replacements(records: list[ReplacementRecord]) -> None:
    print("Replacements")
    print()
    for record in records:
        print("Original")
        print()
        print(record.original_text)
        print()
        print("Replacement")
        print()
        print(record.replacement_text)
        print()
        print("Entity Type")
        print()
        print(record.entity_type)
        print()
        print("Detector")
        print()
        print(record.detector_source)
        print()
        print("Occurrences")
        print()
        print(len(record.occurrences))
        print()
        print("Locations")
        print()
        locations = [location_of(entity) for entity in record.occurrences]
        shown = locations[:3]
        suffix = f" (+{len(locations) - 3} more)" if len(locations) > 3 else ""
        print(", ".join(shown) + suffix)
        print()
        print(DIVIDER)
    print()


def print_summary(records: list[ReplacementRecord]) -> None:
    counts: dict[str, int] = {}
    for record in records:
        counts[record.entity_type] = counts.get(record.entity_type, 0) + len(record.occurrences)

    print(SEPARATOR)
    print()
    print("SUMMARY")
    print()
    for entity_type, label in _SUMMARY_LABELS.items():
        print(f"{label}: {counts.get(entity_type, 0)}")

    for entity_type in sorted(set(counts) - set(_SUMMARY_LABELS)):
        print(f"{entity_type} Replaced: {counts[entity_type]}")

    print()
    print(f"Total Entities Replaced: {sum(counts.values())}")
    print(f"Total Unique Values Replaced: {len(records)}")
    print()


def print_consistency_check(
    records: list[ReplacementRecord],
    original_paragraphs: dict[int, str],
    replaced_paragraphs: dict[int, str],
    original_cells: dict[tuple[int, int, int], str],
    replaced_cells: dict[tuple[int, int, int], str],
) -> bool:
    """Verify that every repeated original value was applied consistently.

    The captured replacement value is already guaranteed unique per key by
    construction (see `capture_replacements`); what this checks is that the
    *applied* text at every one of that key's occurrences actually contains
    that value, catching any splicing bug in `_apply_replacements` itself
    rather than just in the value-generation step.
    """
    print(SEPARATOR)
    print()
    print("CONSISTENCY CHECK")
    print()

    repeated = [record for record in records if len(record.occurrences) > 1]
    if not repeated:
        print("No original value was detected more than once; nothing to check.")
        print()
        return True

    all_consistent = True
    for record in repeated:
        missing_locations: list[str] = []
        for entity in record.occurrences:
            if entity.location_type == PARAGRAPH_LOCATION:
                new_text = replaced_paragraphs.get(entity.paragraph_index, "")
            else:
                key = (entity.table_index, entity.row_index, entity.cell_index)
                new_text = replaced_cells.get(key, "")
            if record.replacement_text not in new_text:
                missing_locations.append(location_of(entity))

        is_consistent = not missing_locations
        all_consistent = all_consistent and is_consistent

        print("Original")
        print()
        print(record.original_text)
        print()
        print("Replacement Used")
        print()
        print(record.replacement_text)
        print()
        print("Occurrences Found")
        print()
        print(len(record.occurrences))
        print()
        print("Status")
        print()
        print("PASS" if is_consistent else "FAIL")
        if missing_locations:
            print(f"  Not found at: {', '.join(missing_locations)}")
        print()
        print(DIVIDER)

    print()
    return all_consistent


def _tables_structure_matches(original: Document, replaced: Document) -> bool:
    if len(original.tables) != len(replaced.tables):
        return False
    for orig_table, new_table in zip(original.tables, replaced.tables):
        if orig_table.id != new_table.id or len(orig_table.rows) != len(new_table.rows):
            return False
        for orig_row, new_row in zip(orig_table.rows, new_table.rows):
            if orig_row.id != new_row.id:
                return False
            if [c.id for c in orig_row.cells] != [c.id for c in new_row.cells]:
                return False
    return True


def _unrelated_cells_unchanged(
    original: Document,
    replaced: Document,
    cell_entities: dict[tuple[int, int, int], list[Entity]],
) -> bool:
    original_cells = _flatten_cells(original)
    replaced_cells = _flatten_cells(replaced)
    return all(
        replaced_cells.get(key) == text
        for key, text in original_cells.items()
        if key not in cell_entities
    )


def print_document_validation(
    original: Document,
    replaced: Document,
    entities: list[Entity],
    eligible_entities: list[Entity],
    overlap_skipped: int,
    missing_keys: list[ReplacementKey],
) -> bool:
    print(SEPARATOR)
    print()
    print("DOCUMENT VALIDATION")
    print()

    paragraph_entities = group_by_paragraph(entities)
    paragraphs_structural = [p.id for p in original.paragraphs] == [p.id for p in replaced.paragraphs]
    paragraphs_unrelated_unchanged = all(
        replaced_p.text == orig_p.text
        for orig_p, replaced_p in zip(original.paragraphs, replaced.paragraphs)
        if orig_p.id not in paragraph_entities
    )
    paragraphs_ok = paragraphs_structural and paragraphs_unrelated_unchanged

    table_structure_ok = _tables_structure_matches(original, replaced)
    cell_entities = group_by_cell(entities)
    cells_unrelated_unchanged = _unrelated_cells_unchanged(original, replaced, cell_entities)

    failed_occurrences = sum(
        1 for e in eligible_entities if (e.entity_type, e.detected_text) in missing_keys
    )
    every_entity_replaced = failed_occurrences == 0
    accounted_for = len(eligible_entities) + overlap_skipped == len(entities)

    print(f"Paragraph replacements: {'PASS' if paragraphs_ok else 'FAIL'}")
    print(f"Table replacements: {'PASS' if table_structure_ok else 'FAIL'}")
    print(f"Cell replacements: {'PASS' if cells_unrelated_unchanged else 'FAIL'}")
    print(f"Every eligible entity replaced: {'PASS' if every_entity_replaced else 'FAIL'}")
    print(f"Every entity accounted for (replaced or legitimately overlap-skipped): {'PASS' if accounted_for else 'FAIL'}")
    print()
    print(f"Entities skipped as genuine overlaps: {overlap_skipped}")
    print()

    if not every_entity_replaced:
        logger.warning(
            "%d entity occurrence(s) across %d distinct value(s) had no replacer output.",
            failed_occurrences,
            len(missing_keys),
        )

    return all(
        [
            paragraphs_ok,
            table_structure_ok,
            cells_unrelated_unchanged,
            every_entity_replaced,
            accounted_for,
        ]
    )


def main() -> None:
    print(SEPARATOR)
    print("REPLACEMENT VALIDATION")
    print(SEPARATOR)
    print()

    document_path = find_input_document()
    print("Input File")
    print()
    print(document_path)
    print()
    print(DIVIDER)
    print()

    logger.info("Reading document: %s", document_path)
    original_document = read_document(document_path)
    print("Document Loaded Successfully")
    print()
    print(DIVIDER)
    print()

    logger.info(
        "Running detector manager over %d paragraphs and %d tables.",
        len(original_document.paragraphs),
        len(original_document.tables),
    )
    entities = analyze_document(original_document)
    logger.info("Detected %d entities.", len(entities))

    logger.info("Running replacement manager over %d entities.", len(entities))
    replaced_document, captured = capture_replacements(original_document, entities)
    print("Replacement Applied (in memory only, no file written)")
    print()
    print(DIVIDER)
    print()

    eligible_entities, overlap_skipped = _eligible_entities(entities)
    records, missing_keys = build_records(eligible_entities, captured)

    print_replacements(records)
    print_summary(records)

    original_paragraphs = {p.id: p.text for p in original_document.paragraphs}
    replaced_paragraphs = {p.id: p.text for p in replaced_document.paragraphs}
    original_cells = _flatten_cells(original_document)
    replaced_cells = _flatten_cells(replaced_document)
    consistency_ok = print_consistency_check(
        records, original_paragraphs, replaced_paragraphs, original_cells, replaced_cells
    )

    structure_ok = print_document_validation(
        original_document, replaced_document, entities, eligible_entities, overlap_skipped, missing_keys
    )

    print(SEPARATOR)
    print()
    if consistency_ok and structure_ok:
        print("Replacement Validation Passed")
    else:
        print("Replacement Validation FAILED")
    print()
    print(SEPARATOR)


if __name__ == "__main__":
    try:
        main()
    except (DocumentReaderError, FileNotFoundError) as exc:
        logger.error("Replacement validation failed: %s", exc)
        print()
        print(SEPARATOR)
        print(f"Replacement Validation FAILED: {exc}")
        print(SEPARATOR)
        sys.exit(1)
