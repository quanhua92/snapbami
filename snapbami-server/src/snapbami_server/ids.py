import secrets
import string

BASE62 = string.digits + string.ascii_lowercase + string.ascii_uppercase


def generate_public_id(length: int = 8) -> str:
    return "".join(secrets.choice(BASE62) for _ in range(length))


def generate_reclaim_key() -> str:
    return f"rk_{secrets.token_urlsafe(24)}"
