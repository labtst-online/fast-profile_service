import logging
import os
import uuid

import boto3
import magic
from fastapi import HTTPException, UploadFile, status

logger = logging.getLogger(__name__)

SIZE_LIMIT_IN_MB = os.getenv("SIZE_LIMIT_IN_KB", "3072")

SUPPORTED_FILE_TYPE = {
    "image/png": "png",
    "image/jpen": "jpeg",
}

AWS_BUCKET = os.getenv("AWS_BUCKET", "fastboosty-profile-bucket")

s3 = boto3.resource("s3")
bucket = s3.Bucket(AWS_BUCKET)


async def s3_upload(contents: bytes, key: str):
    logger.info(f"Uploading {key} to s3")
    bucket.put_object(Key=key, Body=contents)


async def upload_icon(file: UploadFile | None = None):
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file found")

    contents = await file.read()
    file_size = len(contents)

    if 0 < file_size < SIZE_LIMIT_IN_MB * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is too large")

    file_type = magic.from_buffer(buffer=contents, mime=True)
    if file_type not in SUPPORTED_FILE_TYPE:
        logger.info("")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file type: {file_type}."
                f" Supported types are: {SUPPORTED_FILE_TYPE}"
            ),
        )

    await s3_upload(contents=contents, key=f"{uuid.uuid4()}.{SUPPORTED_FILE_TYPE[file_type]}")
