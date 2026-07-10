import re

from snapbami_server.ids import generate_public_id, generate_reclaim_key

BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def test_public_id_length():
    pid = generate_public_id()
    assert len(pid) == 8


def test_public_id_custom_length():
    pid = generate_public_id(12)
    assert len(pid) == 12


def test_public_id_charset():
    pid = generate_public_id(100)
    for c in pid:
        assert c in BASE62


def test_public_id_uniqueness():
    ids = {generate_public_id() for _ in range(1000)}
    assert len(ids) == 1000


def test_reclaim_key_prefix():
    key = generate_reclaim_key()
    assert key.startswith("rk_")


def test_reclaim_key_length():
    key = generate_reclaim_key()
    assert len(key) > 20


def test_reclaim_key_uniqueness():
    keys = {generate_reclaim_key() for _ in range(100)}
    assert len(keys) == 100


def test_reclaim_key_urlsafe():
    key = generate_reclaim_key()
    assert re.match(r"^rk_[A-Za-z0-9_-]+$", key)
