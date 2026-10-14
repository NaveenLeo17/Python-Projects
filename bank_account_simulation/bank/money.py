"""Helpers for safe money handling using Decimal (never float)."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .exceptions import ValidationError

CURRENCY = "Rs."
ZERO = Decimal("0.00")
CENT = Decimal("0.01")
MAX_AMOUNT = Decimal("10000000000.00")  # 1,000 crore safety cap


def parse_amount(value, allow_zero=False):
    """Convert user input to a validated 2-decimal Decimal amount."""
    try:
        amount = Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        raise ValidationError("Please enter a valid number.")
    if not amount.is_finite():
        raise ValidationError("Please enter a valid number.")
    if amount != amount.quantize(CENT, rounding=ROUND_HALF_UP):
        raise ValidationError("Amount can have at most 2 decimal places.")
    if amount > MAX_AMOUNT:
        raise ValidationError("Amount is too large.")
    amount = amount.quantize(CENT)
    if amount < 0 or (amount == 0 and not allow_zero):
        raise ValidationError("Amount must be greater than zero.")
    return amount


def round_money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def fmt(amount):
    return f"{CURRENCY} {amount:,.2f}"
