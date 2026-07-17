"""Document module: reads .docx files into structured Python objects.

This is the only module in the application permitted to import python-docx.
Consumers should use ``read_document`` and the dataclasses in
``document.models`` exclusively.
"""

from document.reader import read_document

__all__ = ["read_document"]
