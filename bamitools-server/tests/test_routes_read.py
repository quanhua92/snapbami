import json
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from bamitools_server.main import app


def _lifespan_mocks():
    return (
        patch("bamitools_server.main.init_pool", new_callable=AsyncMock),
        patch("bamitools_server.main.get_redis", new_callable=AsyncMock),
        patch("bamitools_server.main.close_pool", new_callable=AsyncMock),
    )


def test_health():
    client = TestClient(app)
    m1, m2, m3 = _lifespan_mocks()
    with m1, m2, m3:
        with client:
            resp = client.get("/api/health")
            assert resp.status_code == 200
            assert resp.json() == {"status": "ok"}


def test_read_dashboard_json_cache_hit():
    cached_spec = {"title": "Cached", "layout": []}
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=json.dumps(cached_spec))

    client = TestClient(app)
    m1, m2, m3 = _lifespan_mocks()
    with (
        m1,
        m2,
        m3,
        patch("bamitools_server.api.routes_read.get_redis", return_value=mock_redis),
    ):
        with client:
            resp = client.get("/p/test123.json")
            assert resp.status_code == 200
            assert resp.json() == cached_spec


def test_read_dashboard_json_s3_fallback():
    spec = {"title": "From S3", "layout": []}
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock()

    client = TestClient(app)
    m1, m2, m3 = _lifespan_mocks()
    with (
        m1,
        m2,
        m3,
        patch("bamitools_server.api.routes_read.get_redis", return_value=mock_redis),
        patch(
            "bamitools_server.api.routes_read.get_public_object",
            new_callable=AsyncMock,
            return_value=json.dumps(spec).encode(),
        ),
    ):
        with client:
            resp = client.get("/p/test456.json")
            assert resp.status_code == 200
            assert resp.json()["title"] == "From S3"
            mock_redis.setex.assert_called_once()


def test_read_dashboard_json_not_found():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)

    client = TestClient(app)
    m1, m2, m3 = _lifespan_mocks()
    with (
        m1,
        m2,
        m3,
        patch("bamitools_server.api.routes_read.get_redis", return_value=mock_redis),
        patch(
            "bamitools_server.api.routes_read.get_public_object",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        with client:
            resp = client.get("/p/nonexistent.json")
            assert resp.status_code == 404


def test_read_dashboard_html_cache_hit():
    cached_html = "<html><body>Dashboard</body></html>"
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=cached_html)

    client = TestClient(app)
    m1, m2, m3 = _lifespan_mocks()
    with (
        m1,
        m2,
        m3,
        patch("bamitools_server.api.routes_read.get_redis", return_value=mock_redis),
    ):
        with client:
            resp = client.get("/p/test123")
            assert resp.status_code == 200
            assert "text/html" in resp.headers["content-type"]
            assert "Dashboard" in resp.text


def test_read_dashboard_html_not_found():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)

    client = TestClient(app)
    m1, m2, m3 = _lifespan_mocks()
    with (
        m1,
        m2,
        m3,
        patch("bamitools_server.api.routes_read.get_redis", return_value=mock_redis),
        patch(
            "bamitools_server.api.routes_read.get_public_object",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        with client:
            resp = client.get("/p/nonexistent")
            assert resp.status_code == 404


# ── public_id regex validation ────────────────────────────────────────────


def test_invalid_id_special_chars_json():
    client = TestClient(app)
    m1, m2, m3 = _lifespan_mocks()
    with m1, m2, m3:
        with client:
            resp = client.get("/p/abc;rm.json")
            assert resp.status_code == 400


def test_invalid_id_special_chars_html():
    client = TestClient(app)
    m1, m2, m3 = _lifespan_mocks()
    with m1, m2, m3:
        with client:
            resp = client.get("/p/abc;rm")
            assert resp.status_code == 400


def test_invalid_id_too_long():
    client = TestClient(app)
    m1, m2, m3 = _lifespan_mocks()
    with m1, m2, m3:
        with client:
            resp = client.get("/p/abcdefghijklmnopqrstuvwxyz12345.json")
            assert resp.status_code == 400


def test_invalid_id_spaces():
    client = TestClient(app)
    m1, m2, m3 = _lifespan_mocks()
    with m1, m2, m3:
        with client:
            resp = client.get("/p/abc%20def.json")
            assert resp.status_code == 400


def test_valid_id_8char_base62():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)

    client = TestClient(app)
    m1, m2, m3 = _lifespan_mocks()
    with (
        m1,
        m2,
        m3,
        patch("bamitools_server.api.routes_read.get_redis", return_value=mock_redis),
        patch(
            "bamitools_server.api.routes_read.get_public_object",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        with client:
            resp = client.get("/p/bhExKKWE.json")
            assert resp.status_code == 404  # valid format, just doesn't exist
