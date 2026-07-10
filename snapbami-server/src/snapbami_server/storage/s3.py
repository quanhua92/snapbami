import json
from contextlib import asynccontextmanager

import aioboto3
from botocore.exceptions import ClientError

from snapbami_server.config import settings

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


async def upload_dashboard(public_id: str, json_spec: str, html_loader: str) -> None:
    async with _s3_client() as s3:
        await s3.put_object(
            Bucket=settings.S3_BUCKET,
            Key=f"d/{public_id}",
            Body=html_loader.encode(),
            ContentType="text/html",
            CacheControl="public, max-age=86400",
        )
        await s3.put_object(
            Bucket=settings.S3_BUCKET,
            Key=f"d/{public_id}.json",
            Body=json_spec.encode(),
            ContentType="application/json",
            CacheControl="public, max-age=300",
        )


async def delete_dashboard(public_id: str) -> None:
    async with _s3_client() as s3:
        for key in (f"d/{public_id}", f"d/{public_id}.json"):
            await s3.delete_object(Bucket=settings.S3_BUCKET, Key=key)


async def get_object(key: str) -> bytes | None:
    async with _s3_client() as s3:
        try:
            resp = await s3.get_object(Bucket=settings.S3_BUCKET, Key=key)
            return await resp["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
                return None
            raise


async def get_dashboard_json(public_id: str) -> dict | None:
    data = await get_object(f"d/{public_id}.json")
    if data is None:
        return None
    return json.loads(data)
