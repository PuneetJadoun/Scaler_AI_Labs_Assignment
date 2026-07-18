"""Replaces detected credit card numbers with fake ones."""

from models.entity import Entity
from replacement.faker_provider import fake_credit_card_number


def replace_credit_card(entity: Entity) -> str:
    """Generate a fake replacement for a detected CREDIT_CARD entity."""
    return fake_credit_card_number()
