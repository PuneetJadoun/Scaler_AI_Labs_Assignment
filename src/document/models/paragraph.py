"""Model representing a single paragraph in a document."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Paragraph:
    """A single paragraph (including headings) from a Word document.

    Attributes:
        id: Zero-based index of this paragraph in document order. Stable and
            unique within a single Document, so later pipeline stages can
            refer back to "which paragraph" without touching python-docx.
        text: The full, unmodified text content of the paragraph.
    """

    id: int
    text: str
