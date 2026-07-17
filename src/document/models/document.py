"""Model representing an entire structured document."""

from dataclasses import dataclass
from pathlib import Path

from document.models.paragraph import Paragraph
from document.models.table import Table


@dataclass(frozen=True)
class Document:
    """The complete structured representation of a Word document.

    This is the single object returned by ``reader.read_document`` and the
    only representation of a .docx file that the rest of the application
    (detectors, replacement, evaluation, writer) should ever need to see.

    Attributes:
        source_path: Path to the .docx file this document was read from.
        paragraphs: All top-level paragraphs, in document order.
        tables: All tables, in document order.
    """

    source_path: Path
    paragraphs: list[Paragraph]
    tables: list[Table]
