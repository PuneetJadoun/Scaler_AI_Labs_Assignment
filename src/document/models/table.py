"""Model representing a single table in a document."""

from dataclasses import dataclass

from document.models.cell import Row


@dataclass(frozen=True)
class Table:
    """A single table from a Word document.

    Attributes:
        id: Zero-based index of this table in document order.
        rows: The rows belonging to this table, in top-to-bottom order.
    """

    id: int
    rows: list[Row]
