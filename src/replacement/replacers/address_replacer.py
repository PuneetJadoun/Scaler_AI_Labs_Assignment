"""Replaces detected addresses with fake ones."""

from models.entity import Entity
from replacement.faker_provider import fake_address


def replace_address(entity: Entity) -> str:
    """Generate a fake replacement for a detected LOCATION entity."""
    return fake_address()
