from unittest.mock import AsyncMock, patch

from snapbami_server.storage.s3 import delete_dashboard, upload_dashboard


async def test_upload_dashboard_calls_put_object_twice():
    mock_s3 = AsyncMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_ctx.__aexit__ = AsyncMock(return_value=None)

    with patch("snapbami_server.storage.s3._s3_client", return_value=mock_ctx):
        await upload_dashboard("test123", '{"title":"Test"}', "<html></html>")
        assert mock_s3.put_object.call_count == 2

        first_call = mock_s3.put_object.call_args_list[0]
        assert first_call.kwargs["Key"] == "d/test123"
        assert first_call.kwargs["ContentType"] == "text/html"

        second_call = mock_s3.put_object.call_args_list[1]
        assert second_call.kwargs["Key"] == "d/test123.json"
        assert second_call.kwargs["ContentType"] == "application/json"


async def test_delete_dashboard_calls_delete_twice():
    mock_s3 = AsyncMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_ctx.__aexit__ = AsyncMock(return_value=None)

    with patch("snapbami_server.storage.s3._s3_client", return_value=mock_ctx):
        await delete_dashboard("test123")
        assert mock_s3.delete_object.call_count == 2
