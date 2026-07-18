"""Central Faker provider for the Replacement Module.

Every replacer asks for fake values here instead of importing Faker
directly. This gives the module exactly one place that owns the Faker
dependency, one place to change locale/providers later, and one place to
handle a missing Faker installation.
"""

from functools import lru_cache


class FakerUnavailableError(RuntimeError):
    """Raised when the `faker` package is not installed."""


@lru_cache(maxsize=1)
def _get_faker():
    """Lazily build and cache the Faker instance."""
    try:
        from faker import Faker
    except ImportError as exc:
        raise FakerUnavailableError(
            "faker is not installed. Install it with 'pip install Faker'."
        ) from exc
    return Faker()


def fake_person_name() -> str:
    """Generate a fake full name."""
    return _get_faker().name()


def fake_email() -> str:
    """Generate a fully fake email address (local part and domain)."""
    return _get_faker().email()


def fake_email_local_part() -> str:
    """Generate a fake email local part (the part before '@')."""
    return _get_faker().user_name()


def fake_phone_number() -> str:
    """Generate a fake phone number."""
    return _get_faker().phone_number()


def fake_company_name() -> str:
    """Generate a fake company name."""
    return _get_faker().company()


def fake_address() -> str:
    """Generate a fake single-line mailing address."""
    return _get_faker().address().replace("\n", ", ")


def fake_ssn() -> str:
    """Generate a fake Social Security Number."""
    return _get_faker().ssn()


def fake_credit_card_number() -> str:
    """Generate a fake credit card number."""
    return _get_faker().credit_card_number()


def fake_date_of_birth() -> str:
    """Generate a fake date of birth, formatted as 'Month DD, YYYY'."""
    return _get_faker().date_of_birth().strftime("%B %d, %Y")


def fake_ip_address() -> str:
    """Generate a fake IPv4 address."""
    return _get_faker().ipv4()
