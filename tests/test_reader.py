"""Standalone validation script for the Document Reader.

This is NOT a pytest/unittest suite. It is a simple executable script used
to validate the Document Module's architecture end-to-end against a real
.docx file before the Detector module is built on top of it.

Usage:
    python tests/test_reader.py [path/to/file.docx]

If no path is given, the first .docx file found in input/ is used.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from document.models.document import Document  # noqa: E402
from document.models.paragraph import Paragraph  # noqa: E402
from document.models.table import Table  # noqa: E402
from document.reader import DocumentReaderError, read_document  # noqa: E402

INPUT_DIR = PROJECT_ROOT / "input"
PREVIEW_COUNT = 3
SEPARATOR = "=" * 60
DIVIDER = "-" * 60


def find_input_document() -> Path:
    """Return the document to test: a CLI arg, or the first .docx in input/."""
    if len(sys.argv) > 1:
        return Path(sys.argv[1])

    candidates = sorted(INPUT_DIR.glob("*.docx"))
    if not candidates:
        raise FileNotFoundError(
            f"No .docx file found in '{INPUT_DIR}'. "
            f"Place a document there or pass a path as an argument."
        )
    return candidates[0]


def print_header(title: str) -> None:
    print(SEPARATOR)
    print(title)
    print(SEPARATOR)
    print()


def print_document_summary(document: Document) -> None:
    empty_paragraphs = sum(1 for p in document.paragraphs if not p.text.strip())
    total_cells = sum(len(row.cells) for table in document.tables for row in table.rows)
    empty_cells = sum(
        1
        for table in document.tables
        for row in table.rows
        for cell in row.cells
        if not cell.text.strip()
    )

    print(f"Source          : {document.source_path}")
    print(f"Paragraphs      : {len(document.paragraphs)}  ({empty_paragraphs} empty)")
    print(f"Tables          : {len(document.tables)}")
    print(f"Total cells     : {total_cells}  ({empty_cells} empty)")
    print()

    for table in document.tables:
        columns = len(table.rows[0].cells) if table.rows else 0
        print(f"Table {table.id}")
        print(f"  Rows    : {len(table.rows)}")
        print(f"  Columns : {columns}")
    print()


def print_preview_paragraphs(paragraphs: list[Paragraph]) -> None:
    print(DIVIDER)
    print(f"First {min(PREVIEW_COUNT, len(paragraphs))} Paragraphs")
    print(DIVIDER)
    if not paragraphs:
        print("(document has no paragraphs)")
    for paragraph in paragraphs[:PREVIEW_COUNT]:
        text = paragraph.text if paragraph.text.strip() else "(empty)"
        print(f"[{paragraph.id}] {text}")
    print()


def print_preview_table_cells(tables: list[Table]) -> None:
    print(DIVIDER)
    print("First Table Cells")
    print(DIVIDER)
    if not tables:
        print("(document has no tables)")
        print()
        return

    first_table = tables[0]
    count = 0
    for row in first_table.rows:
        for cell in row.cells:
            if count >= PREVIEW_COUNT:
                break
            text = cell.text if cell.text.strip() else "(empty)"
            print(f"Table {first_table.id} | Row {row.id} | Cell {cell.id}: {text}")
            count += 1
        if count >= PREVIEW_COUNT:
            break
    print()


def validate_document(document: Document) -> None:
    """Structural assertions. Raises AssertionError with a clear message on failure."""
    assert isinstance(document, Document), "read_document did not return a Document"
    assert isinstance(document.paragraphs, list), "paragraphs must be a list"
    assert isinstance(document.tables, list), "tables must be a list"

    for paragraph in document.paragraphs:
        assert isinstance(paragraph, Paragraph), f"Not a Paragraph: {paragraph!r}"
        assert isinstance(paragraph.text, str), f"Paragraph {paragraph.id} text is not str"

    for table in document.tables:
        assert isinstance(table, Table), f"Not a Table: {table!r}"
        row_lengths = {len(row.cells) for row in table.rows}
        assert len(row_lengths) <= 1, (
            f"Table {table.id} has rows with inconsistent cell counts: {row_lengths}"
        )
        for row in table.rows:
            for cell in row.cells:
                assert isinstance(cell.text, str), (
                    f"Table {table.id} Row {row.id} Cell {cell.id} text is not str"
                )


def main() -> None:
    print_header("Document Reader Test")

    document_path = find_input_document()
    print(f"Loading: {document_path}")
    print()

    document = read_document(document_path)
    validate_document(document)

    print_header("Document Summary")
    print_document_summary(document)
    print_preview_paragraphs(document.paragraphs)
    print_preview_table_cells(document.tables)

    print(SEPARATOR)
    print("Document Reader Test Passed")
    print(SEPARATOR)


if __name__ == "__main__":
    try:
        main()
    except (DocumentReaderError, FileNotFoundError, AssertionError) as exc:
        print()
        print(SEPARATOR)
        print(f"Document Reader Test FAILED: {exc}")
        print(SEPARATOR)
        sys.exit(1)
