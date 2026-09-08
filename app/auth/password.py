import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, stored: str) -> bool:
    try:
        return _hasher.verify(stored, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


# Reason: a login that does not exist has no hash to verify, and skipping
# Argon2id would answer far faster than a real login does, telling an
# attacker which logins exist. The absent login verifies against this hash
# instead, so both paths cost the same. The secret behind it is thrown away:
# nothing can match it.
ABSENT_USER_HASH = hash_password(secrets.token_hex(32))


def verify_absent_user(plain: str) -> bool:
    return verify_password(plain, ABSENT_USER_HASH)
