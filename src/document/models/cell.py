"""Models representing table rows and cells."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Cell:
    """A single table cell.

    Attributes:
        id: Zero-based index of this cell within its parent row.
        text: The full, unmodified text content of the cell.
    """

    id: int
    text: str


@dataclass(frozen=True)
class Row:
    """A single table row, made up of an ordered list of cells.

    Attributes:
        id: Zero-based index of this row within its parent table.
        cells: The cells belonging to this row, in column order.
    """

    id: int
    cells: list[Cell]
