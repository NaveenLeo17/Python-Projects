"""PIN hashing and validation (PBKDF2-HMAC-SHA256 with per-account salt)."""
import hashlib
import hmac
import os
import re

from .exceptions import ValidationError

ITERATIONS = 200_000
MAX_FAILED_ATTEMPTS = 3
LOCKOUT_MINUTES = 5


def validate_pin_format(pin):
    if not isinstance(pin, str) or not re.fullmatch(r"\d{4,6}", pin):
        raise ValidationError("PIN must be 4 to 6 digits.")
    if len(set(pin)) == 1:
        raise ValidationError("PIN is too weak (all digits are the same).")
    digits = [int(c) for c in pin]
    steps = {digits[i + 1] - digits[i] for i in range(len(digits) - 1)}
    if steps in ({1}, {-1}):
        raise ValidationError("PIN is too weak (sequential digits).")


def hash_pin(pin, salt=None):
    """Return (salt_hex, hash_hex). A new random salt is made if none given."""
    salt = salt if salt is not None else os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, ITERATIONS)
    return salt.hex(), digest.hex()


def verify_pin(pin, salt_hex, hash_hex):
    _, candidate = hash_pin(pin, bytes.fromhex(salt_hex))
    return hmac.compare_digest(candidate, hash_hex)
