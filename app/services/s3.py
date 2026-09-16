import re
from functools import lru_cache
from typing import Optional, Tuple
from urllib.parse import unquote, urlparse

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings

_S3_VIRTUAL_HOST = re.compile(
    r"^(?P<bucket>.+)\.s3(?:[.-](?P<region>[a-z0-9-]+))?\.amazonaws\.com$"
)
_S3_PATH_HOST = re.compile(
    r"^s3(?:[.-](?P<region>[a-z0-9-]+))?\.amazonaws\.com$"
)


@lru_cache
def get_s3_client():
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        raise RuntimeError("AWS S3 credentials are not configured")
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def parse_s3_location(url: str) -> Optional[Tuple[str, str]]:
    parsed = urlparse(url)
    if parsed.scheme == "s3":
        bucket = parsed.netloc
        key = unquote(parsed.path.lstrip("/"))
        return (bucket, key) if bucket and key else None

    host = parsed.netloc.split(":")[0]
    path = unquote(parsed.path.lstrip("/"))

    public_base = (settings.AWS_S3_PUBLIC_BASE_URL or "").rstrip("/")
    if public_base and url.startswith(public_base) and settings.AWS_S3_BUCKET:
        key = unquote(url[len(public_base) :].lstrip("/"))
        return (settings.AWS_S3_BUCKET, key) if key else None

    path_match = _S3_PATH_HOST.fullmatch(host)
    if path_match:
        bucket, _, key = path.partition("/")
        return (bucket, key) if bucket and key else None

    virtual_match = _S3_VIRTUAL_HOST.fullmatch(host)
    if virtual_match and path:
        return virtual_match.group("bucket"), path

    return None


def download_s3_object(bucket: str, key: str) -> bytes:
    try:
        response = get_s3_client().get_object(Bucket=bucket, Key=key)
        body = response["Body"].read()
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Failed to download S3 object s3://{bucket}/{key}") from exc

    if settings.UPLOAD_MAX_BYTES and len(body) > settings.UPLOAD_MAX_BYTES:
        raise RuntimeError(
            f"S3 object s3://{bucket}/{key} exceeds UPLOAD_MAX_BYTES"
        )
    return body
