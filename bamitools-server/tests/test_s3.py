from unittest.mock import AsyncMock, patch

from bamitools_server.config import settings
from bamitools_server.storage.s3 import (
    delete_private_object,
    delete_public_object,
    get_private_object,
    get_public_object,
    get_public_object_json,
    upload_private_object,
    upload_public_object,
)


def _mock_client():
    mock_s3 = AsyncMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_ctx.__aexit__ = AsyncMock(return_value=None)
    return mock_s3, mock_ctx


# ── Public bucket: keys at root ────────────────────────────────────────────


async def test_upload_public_object_root_key():
    mock_s3, mock_ctx = _mock_client()
    with patch("bamitools_server.storage.s3._s3_client", return_value=mock_ctx):
        await upload_public_object(
            "test123", b"<html></html>", content_type="text/html"
        )
    mock_s3.put_object.assert_awaited_once()
    kwargs = mock_s3.put_object.call_args.kwargs
    assert kwargs["Key"] == "test123"
    assert kwargs["Bucket"] == settings.S3_PUBLIC_BUCKET
    assert kwargs["ContentType"] == "text/html"


async def test_upload_public_object_with_cache_control():
    mock_s3, mock_ctx = _mock_client()
    with patch("bamitools_server.storage.s3._s3_client", return_value=mock_ctx):
        await upload_public_object(
            "abc",
            b"data",
            content_type="application/json",
            cache_control="public, max-age=300",
        )
    kwargs = mock_s3.put_object.call_args.kwargs
    assert kwargs["CacheControl"] == "public, max-age=300"


async def test_delete_public_object_removes_page_and_spec():
    mock_s3, mock_ctx = _mock_client()
    with patch("bamitools_server.storage.s3._s3_client", return_value=mock_ctx):
        await delete_public_object("test123")
    assert mock_s3.delete_object.call_count == 2
    keys = [c.kwargs["Key"] for c in mock_s3.delete_object.call_args_list]
    assert keys == ["test123", "test123.json"]
    for c in mock_s3.delete_object.call_args_list:
        assert c.kwargs["Bucket"] == settings.S3_PUBLIC_BUCKET


async def test_delete_public_object_spec_only_optional():
    mock_s3, mock_ctx = _mock_client()
    with patch("bamitools_server.storage.s3._s3_client", return_value=mock_ctx):
        await delete_public_object("test123", include_spec=False)
    assert mock_s3.delete_object.call_count == 1
    assert mock_s3.delete_object.call_args.kwargs["Key"] == "test123"


async def test_get_public_object_root_key():
    mock_s3, mock_ctx = _mock_client()
    mock_s3.get_object = AsyncMock(
        return_value={"Body": AsyncMock(read=AsyncMock(return_value=b"<html></html>"))}
    )
    with patch("bamitools_server.storage.s3._s3_client", return_value=mock_ctx):
        data = await get_public_object("test123")
    assert data == b"<html></html>"
    kwargs = mock_s3.get_object.call_args.kwargs
    assert kwargs["Key"] == "test123"
    assert kwargs["Bucket"] == settings.S3_PUBLIC_BUCKET


async def test_get_public_object_json():
    body = b'{"title":"Hi"}'
    mock_s3, mock_ctx = _mock_client()
    mock_s3.get_object = AsyncMock(
        return_value={"Body": AsyncMock(read=AsyncMock(return_value=body))}
    )
    with patch("bamitools_server.storage.s3._s3_client", return_value=mock_ctx):
        spec = await get_public_object_json("test123")
    assert spec == {"title": "Hi"}
    assert mock_s3.get_object.call_args.kwargs["Key"] == "test123.json"


# ── Private bucket: keys {workspace_id}/{filepath} ─────────────────────────


async def test_upload_private_object_workspace_key():
    mock_s3, mock_ctx = _mock_client()
    with patch("bamitools_server.storage.s3._s3_client", return_value=mock_ctx):
        await upload_private_object(
            "ws-uuid-1", "notes/todo.md", b"# Todo", content_type="text/markdown"
        )
    kwargs = mock_s3.put_object.call_args.kwargs
    assert kwargs["Key"] == "ws-uuid-1/notes/todo.md"
    assert kwargs["Bucket"] == settings.S3_PRIVATE_BUCKET
    assert kwargs["ContentType"] == "text/markdown"


async def test_get_private_object_workspace_key():
    mock_s3, mock_ctx = _mock_client()
    mock_s3.get_object = AsyncMock(
        return_value={"Body": AsyncMock(read=AsyncMock(return_value=b"data"))}
    )
    with patch("bamitools_server.storage.s3._s3_client", return_value=mock_ctx):
        data = await get_private_object("ws-1", "reports/q1.csv")
    assert data == b"data"
    kwargs = mock_s3.get_object.call_args.kwargs
    assert kwargs["Key"] == "ws-1/reports/q1.csv"
    assert kwargs["Bucket"] == settings.S3_PRIVATE_BUCKET


async def test_delete_private_object_workspace_key():
    mock_s3, mock_ctx = _mock_client()
    with patch("bamitools_server.storage.s3._s3_client", return_value=mock_ctx):
        await delete_private_object("ws-1", "draft.md")
    mock_s3.delete_object.assert_awaited_once()
    kwargs = mock_s3.delete_object.call_args.kwargs
    assert kwargs["Key"] == "ws-1/draft.md"
    assert kwargs["Bucket"] == settings.S3_PRIVATE_BUCKET
