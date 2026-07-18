"""Replaces detected email addresses with fake ones, preserving the domain.

Keeping the original domain (e.g. "@gmail.com") while replacing only the
local part keeps the replacement's shape realistic and recognizable as
still being "an email like the original one".
"""

from models.entity import Entity
from replacement.faker_provider import fake_email, fake_email_local_part


def replace_email(entity: Entity) -> str:
    """Generate a fake replacement for a detected EMAIL entity."""
    original = entity.detected_text
    if "@" not in original:
        return fake_email()

    domain = original.rsplit("@", 1)[-1]
    return f"{fake_email_local_part()}@{domain}"
