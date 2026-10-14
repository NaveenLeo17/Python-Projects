"""Simple admin authentication using a salted-hash credential file."""

import json
import os
import hashlib
import secrets
import getpass

from .exceptions import AuthenticationError, StorageError

CRED_PATH = "data/admin.json"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"  # only used to bootstrap the very first run


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _ensure_credentials_file() -> None:
    os.makedirs(os.path.dirname(CRED_PATH) or ".", exist_ok=True)
    if not os.path.exists(CRED_PATH):
        salt = secrets.token_hex(8)
        data = {
            "username": DEFAULT_USERNAME,
            "salt": salt,
            "password_hash": _hash_password(DEFAULT_PASSWORD, salt),
        }
        try:
            with open(CRED_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as exc:
            raise StorageError(f"Could not create credentials file: {exc}") from exc


def _load_credentials() -> dict:
    _ensure_credentials_file()
    try:
        with open(CRED_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError(f"Could not read credentials file: {exc}") from exc


def change_password(new_password: str) -> None:
    creds = _load_credentials()
    salt = secrets.token_hex(8)
    creds["salt"] = salt
    creds["password_hash"] = _hash_password(new_password, salt)
    try:
        with open(CRED_PATH, "w", encoding="utf-8") as f:
            json.dump(creds, f, indent=2)
    except OSError as exc:
        raise StorageError(f"Could not update credentials file: {exc}") from exc


def login(max_attempts: int = 3) -> bool:
    """Prompt for username/password. Returns True on success, raises on failure."""
    creds = _load_credentials()

    for attempt in range(1, max_attempts + 1):
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")

        candidate_hash = _hash_password(password, creds["salt"])
        if username == creds["username"] and candidate_hash == creds["password_hash"]:
            return True

        remaining = max_attempts - attempt
        if remaining > 0:
            print(f"Invalid credentials. {remaining} attempt(s) remaining.")

    raise AuthenticationError("Too many failed login attempts.")
