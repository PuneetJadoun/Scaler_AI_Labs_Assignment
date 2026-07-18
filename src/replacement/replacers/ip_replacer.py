"""Replaces detected IP addresses with fake ones."""

from models.entity import Entity
from replacement.faker_provider import fake_ip_address


def replace_ip(entity: Entity) -> str:
    """Generate a fake replacement for a detected IP_ADDRESS entity."""
    return fake_ip_address()
