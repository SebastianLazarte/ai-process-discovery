"""Decimal helpers.

Calculations keep full ``Decimal`` precision. Rounding happens only when a value
is presented (API response, blueprint), through the ``present_*`` functions.
"""

from decimal import ROUND_HALF_UP, Decimal

from app.domain.errors import DomainValidationError

ZERO = Decimal(0)
ONE = Decimal(1)

_CENTS = Decimal("0.01")
_TENTHS = Decimal("0.1")


def to_decimal(value: object, field: str) -> Decimal:
    """Coerce ints and numeric strings to Decimal. Floats are rejected on purpose."""
    if isinstance(value, bool):
        raise DomainValidationError(field, "must be a number, not a boolean")
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, int):
        result = Decimal(value)
    elif isinstance(value, str):
        try:
            result = Decimal(value)
        except ArithmeticError as exc:
            raise DomainValidationError(field, f"invalid number {value!r}") from exc
    else:
        raise DomainValidationError(
            field, f"must be Decimal, int or numeric string, got {type(value).__name__}"
        )
    if not result.is_finite():
        raise DomainValidationError(field, "must be a finite number")
    return result


def present_money(value: Decimal) -> Decimal:
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP)


def present_hours(value: Decimal) -> Decimal:
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP)


def present_ratio(value: Decimal) -> Decimal:
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP)


def present_score(value: Decimal) -> Decimal:
    return value.quantize(_TENTHS, rounding=ROUND_HALF_UP)
