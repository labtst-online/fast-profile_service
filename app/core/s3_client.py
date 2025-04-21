import logging
import mimetypes
import uuid
from contextlib import asynccontextmanager

import aioboto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Client:
    """
    AWS Client
    """

    def __init__(
        self,
        AWS_ACCESS_KEY_ID: str,
        AWS_SECRET_ACCESS_KEY: str,
        BUCKET_NAME: str,
        REGION_NAME: str,
    ):
        """
        Initializes the S3Client
        """
        self.aws_access_key_id = AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = AWS_SECRET_ACCESS_KEY
        self.bucket_name = BUCKET_NAME
        self.region_name = REGION_NAME

        # Creating async session
        self.session = aioboto3.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
        )
        logger.info(
            f"S3Client initialized for bucket '{self.bucket_name}' in region '{self.region_name}'"
        )

    @asynccontextmanager
    async def _get_client(self):
        """
        Provides an S3 client
        """
        try:
            async with self.session.client(service_name="s3") as s3_client:
                yield s3_client
        except ClientError as e:
            logger.exception("Failed to create S3 client")
            raise Exception(f"Unexpected error creating S3 client: {e}")
        except Exception as e:
            logger.exception("Failed to create S3 client")
            raise Exception(f"Unexpected error creating S3 client: {e}")

    def _get_file_extension(self, content_type: str | None, filename: str | None) -> str:
        """
        Determines the appropriate file extension based on content type or filename
        """
        extension: str | None = None

        if content_type:
            extension = mimetypes.guess_extension(content_type)
            logger.info(f"Extension {extension} recieved successful")

        if filename and not extension:
            extension = mimetypes.guess_extension(filename)
            logger.debug(f"Guessed extension '{extension}' from filename '{filename}'")

        if extension:
            if extension == ".jpe":
                logger.debug("Normalizing extension '.jpe' to '.jpeg'")
                return ".jpeg"
            if not extension.startswith("."):
                extension = "." + extension
            return extension

        logger.warning(f"Could not determine file extension for content_type='{content_type}'")
        raise Exception(content_type=content_type, filename=filename)

    async def upload_file(
        self,
        file_content: bytes,
        content_type: str,
        prefix: str,
        original_filename: str | None = None,
    ) -> str:
        """
        Uploads file content to the S3 bucket with a unique name
        """
        file_uuid = uuid.uuid4()

        try:
            extension = self._get_file_extension(content_type, original_filename)
            logger.info(f"Determined extension: {extension}")
        except Exception as e:
            logger.info(f"Failed to determine file extension for content type {content_type}.")
            raise Exception(f"Unexpected error creating S3 client: {e}")

        if prefix and not prefix.endswith("/"):
            prefix += "/"
            logger.debug(f"Prefix was changed on {prefix}")

        logger.info(f"The current prefix is {prefix}")

        object_key = f"{prefix}{file_uuid}{extension}"
        logger.info(
            f"Attempting to upload to S3: Bucket='{self.bucket_name}',"
            f" Key='{object_key}', ContentType='{content_type}'"
        )

        try:
            async with self._get_client() as s3_client:
                await s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_key,
                    Body=file_content,
                    ContentType=content_type,
                )
            logger.info(f"Successfully uploaded file to {object_key}")
            return str(file_uuid), extension

        except ClientError as e:
            logger.error(f"S3 ClientError during upload to {object_key}: {e}", exc_info=True)
            raise Exception(bucket=self.bucket_name, key=object_key, original_exception=e)
        except Exception as e:
            logger.error(f"Unexpected error during upload to {object_key}: {e}", exc_info=True)
            raise Exception(f"An unexpected error occurred during upload: {e}")

    async def get_file_url(
        self,
        file_uuid: str,
        extension: str,
        prefix: str,
        expires_in: int = 3600,  # 1 hour by default
    ) -> str:
        """
        Generates a pre-signed URL for securely accessing an S3 object via GET request
        """
        object_key = f"{prefix}/{file_uuid}{extension}"

        try:
            async with self._get_client() as s3_client:
                presigned_url = await s3_client.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": self.bucket_name, "Key": object_key},
                    ExpiresIn=expires_in,
                )
            logger.info(f"Generated pre-signed URL for {object_key}")
            return presigned_url

        except ClientError as e:
            logger.error(
                f"S3 pre-signed URL generation failed for Key='{object_key}': {e}", exc_info=True
            )
            raise Exception(bucket=self.bucket_name, key=object_key, original_exception=e)
        except Exception as e:
            logger.error(f"Unexpected error during upload to {object_key}: {e}", exc_info=True)
            raise Exception(f"An unexpected error occurred during upload: {e}")
