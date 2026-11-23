"""Administrator account management for SecureVault.

Administrator credentials are separate from the legacy vault master password.
Only salted PBKDF2 password verifiers are persisted in SQLite.
"""

import hashlib
import hmac
import os
from typing import Optional

import db_manager


PBKDF2_ITERATIONS = 310_000
SALT_LENGTH = 16
MIN_PASSWORD_LENGTH = 8


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=32,
    )


def count_accounts() -> int:
    return db_manager.count_admin_accounts()


def setup_accounts(
    admin1_name: str,
    admin1_password: str,
    admin2_name: str,
    admin2_password: str,
) -> None:
    values = (
        (1, admin1_name, admin1_password),
        (2, admin2_name, admin2_password),
    )
    seen_names = set()
    for number, name, password in values:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError(f"Admin {number} name is required.")
        if clean_name.casefold() in seen_names:
            raise ValueError("Administrator names must be unique.")
        seen_names.add(clean_name.casefold())
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Admin {number} password must be at least "
                f"{MIN_PASSWORD_LENGTH} characters long."
            )

    if count_accounts():
        raise ValueError("Administrator accounts are already configured.")

    for number, name, password in values:
        salt = os.urandom(SALT_LENGTH)
        db_manager.insert_admin_account(
            number,
            name.strip(),
            salt,
            _hash_password(password, salt),
        )


def authenticate(admin_number: int, password: str) -> Optional[dict]:
    if admin_number not in (1, 2) or not password:
        return None
    account = db_manager.get_admin_account(admin_number)
    if account is None:
        return None
    stored_salt, stored_hash = account["salt"], account["password_hash"]
    candidate = _hash_password(password, stored_salt)
    if not hmac.compare_digest(candidate, stored_hash):
        return None
    return {
        "number": admin_number,
        "name": account["name"],
        "password": password,
    }
