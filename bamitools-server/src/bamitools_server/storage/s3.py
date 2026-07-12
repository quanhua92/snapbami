import json
from contextlib import asynccontextmanager

import aioboto3
from botocore.exceptions import ClientError

from bamitools_server.config import settings

_session = aioboto3.Session()


@asynccontextmanager
async def _s3_client():
    async with _session.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL or None,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
    ) as client:
        yield client


async def _get(bucket: str, key: str) -> bytes | None:
    async with _s3_client() as s3:
        try:
            resp = await s3.get_object(Bucket=bucket, Key=key)
            return await resp["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
                return None
            raise


async def _put(
    bucket: str,
    key: str,
    body: bytes,
    *,
    content_type: str,
    cache_control: str | None = None,
) -> None:
    extra: dict = {"ContentType": content_type}
    if cache_control is not None:
        extra["CacheControl"] = cache_control
    async with _s3_client() as s3:
        await s3.put_object(Bucket=bucket, Key=key, Body=body, **extra)


async def _delete(bucket: str, key: str) -> None:
    async with _s3_client() as s3:
        await s3.delete_object(Bucket=bucket, Key=key)


# ── Public bucket (keys at root: {public_id}, {public_id}.json) ────────────


async def get_public_object(public_id: str) -> bytes | None:
    return await _get(settings.S3_PUBLIC_BUCKET, public_id)


async def get_public_object_json(public_id: str) -> dict | None:
    data = await _get(settings.S3_PUBLIC_BUCKET, f"{public_id}.json")
    if data is None:
        return None
    return json.loads(data)


async def upload_public_object(
    public_id: str,
    body: bytes,
    *,
    content_type: str,
    cache_control: str | None = None,
) -> None:
    await _put(
        settings.S3_PUBLIC_BUCKET,
        public_id,
        body,
        content_type=content_type,
        cache_control=cache_control,
    )


async def delete_public_object(public_id: str, *, include_spec: bool = True) -> None:
    await _delete(settings.S3_PUBLIC_BUCKET, public_id)
    if include_spec:
        await _delete(settings.S3_PUBLIC_BUCKET, f"{public_id}.json")


# ── Private bucket (keys: {workspace_id}/{filepath}) ───────────────────────


def _private_key(workspace_id: str, filepath: str) -> str:
    return f"{workspace_id}/{filepath}"


async def get_private_object(workspace_id: str, filepath: str) -> bytes | None:
    return await _get(settings.S3_PRIVATE_BUCKET, _private_key(workspace_id, filepath))


async def upload_private_object(
    workspace_id: str,
    filepath: str,
    body: bytes,
    *,
    content_type: str,
) -> None:
    await _put(
        settings.S3_PRIVATE_BUCKET,
        _private_key(workspace_id, filepath),
        body,
        content_type=content_type,
    )


async def delete_private_object(workspace_id: str, filepath: str) -> None:
    await _delete(settings.S3_PRIVATE_BUCKET, _private_key(workspace_id, filepath))
