import os
import asyncio
import logging
from typing import Optional, BinaryIO
from backend.app.core.config import settings
from backend.app.services.storage.base import BaseStorageService

logger = logging.getLogger("qagent.storage.s3")

class S3StorageService(BaseStorageService):
    """
    S3 / Cloud Object Storage provider for production deployments.
    Supports AWS S3, MinIO, Cloudflare R2, Google Cloud Storage (S3-interop), and Ceph.
    """
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: Optional[str] = None
    ):
        self.bucket_name = bucket_name or settings.S3_BUCKET
        self.endpoint_url = (endpoint_url or settings.S3_ENDPOINT_URL) or None
        self.access_key = (access_key or settings.S3_ACCESS_KEY_ID) or None
        self.secret_key = (secret_key or settings.S3_SECRET_ACCESS_KEY) or None
        self.region = region or settings.S3_REGION or "us-east-1"
        self._local_cache_dir = os.path.abspath(os.path.join(settings.STORAGE_DIR, "_s3_cache"))
        os.makedirs(self._local_cache_dir, exist_ok=True)

    def _get_client(self):
        import boto3
        from botocore.config import Config

        session = boto3.session.Session()
        client_kwargs = {
            "service_name": "s3",
            "region_name": self.region,
            "config": Config(signature_version="s3v4", s3={"addressing_style": "auto"})
        }
        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url
        if self.access_key and self.secret_key:
            client_kwargs["aws_access_key_id"] = self.access_key
            client_kwargs["aws_secret_access_key"] = self.secret_key

        return session.client(**client_kwargs)

    async def upload_file(
        self,
        file_obj: BinaryIO,
        storage_key: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        clean_key = storage_key.lstrip("/\\")

        def _sync_upload():
            client = self._get_client()
            if hasattr(file_obj, "seek"):
                try:
                    file_obj.seek(0)
                except Exception:
                    pass
            client.upload_fileobj(
                file_obj,
                self.bucket_name,
                clean_key,
                ExtraArgs={"ContentType": content_type}
            )

        await asyncio.to_thread(_sync_upload)
        return clean_key

    async def upload_bytes(
        self,
        data: bytes,
        storage_key: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        clean_key = storage_key.lstrip("/\\")

        def _sync_upload():
            client = self._get_client()
            client.put_object(
                Bucket=self.bucket_name,
                Key=clean_key,
                Body=data,
                ContentType=content_type
            )

        await asyncio.to_thread(_sync_upload)
        return clean_key

    async def download_bytes(self, storage_key: str) -> bytes:
        clean_key = storage_key.lstrip("/\\")

        def _sync_download() -> bytes:
            client = self._get_client()
            response = client.get_object(Bucket=self.bucket_name, Key=clean_key)
            return response["Body"].read()

        return await asyncio.to_thread(_sync_download)

    async def delete_file(self, storage_key: str) -> bool:
        clean_key = storage_key.lstrip("/\\")

        def _sync_delete() -> bool:
            client = self._get_client()
            client.delete_object(Bucket=self.bucket_name, Key=clean_key)
            return True

        try:
            return await asyncio.to_thread(_sync_delete)
        except Exception as e:
            logger.warning(f"Failed to delete {clean_key} from S3 bucket {self.bucket_name}: {e}")
            return False

    async def file_exists(self, storage_key: str) -> bool:
        clean_key = storage_key.lstrip("/\\")

        def _sync_exists() -> bool:
            client = self._get_client()
            try:
                client.head_object(Bucket=self.bucket_name, Key=clean_key)
                return True
            except Exception:
                return False

        return await asyncio.to_thread(_sync_exists)

    async def get_local_path(self, storage_key: str) -> str:
        clean_key = storage_key.lstrip("/\\")
        cached_path = os.path.join(self._local_cache_dir, clean_key.replace("/", "_"))
        if not os.path.exists(cached_path):
            data = await self.download_bytes(clean_key)
            with open(cached_path, "wb") as f:
                f.write(data)
        return cached_path

    async def get_file_url(self, storage_key: str, expires_in: int = 3600) -> Optional[str]:
        clean_key = storage_key.lstrip("/\\")

        def _sync_presign() -> str:
            client = self._get_client()
            return client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": clean_key},
                ExpiresIn=expires_in
            )

        try:
            return await asyncio.to_thread(_sync_presign)
        except Exception as e:
            logger.warning(f"Could not generate presigned URL for {clean_key}: {e}")
            return None
